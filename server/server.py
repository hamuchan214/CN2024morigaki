import asyncio
import json
import time
from database import AsyncDatabase
from logging import getLogger, DEBUG, INFO
import colorlog
from utils import generate_session_id
import socket

# colorlog用の設定
LOG_FORMAT = "%(log_color)s%(asctime)s - %(name)s - %(levelname)s - %(message)s"
LOG_LEVEL = DEBUG  # 開発環境ではDEBUG、本番ではINFOに変更可能
LOG_DATE_FORMAT = "%H:%M:%S"


def setup_logger():
    handler = colorlog.StreamHandler()
    formatter = colorlog.ColoredFormatter(LOG_FORMAT)
    handler.setFormatter(formatter)
    logger = getLogger(__name__)
    logger.addHandler(handler)
    logger.setLevel(LOG_LEVEL)
    return logger


class ChatServer:
    def __init__(self, host="127.0.0.1", port=6001):
        self.host = host
        self.port = port
        self.db = AsyncDatabase("chat.db")
        self.sessions = {}
        self.clients = []
        self.clients_lock = asyncio.Lock()  # スレッドセーフのためのロック
        self.logger = setup_logger()

    # セッションを作成
    def create_session(self, user_id):
        session_id = generate_session_id(user_id)
        expiration_time = time.time() + 3600
        self.sessions[session_id] = (user_id, expiration_time)
        self.logger.debug(f"Session created: {self.sessions}")
        return session_id

    # セッションの有効期限を確認
    def validate_session(self, session_id):
        session = self.sessions.get(session_id)
        if session:
            user_id, expiration_time = session
            if time.time() < expiration_time:
                return user_id
            else:
                del self.sessions[session_id]
        return None

    async def start(self):
        """サーバーを起動する。"""
        setup_result = await self.db.setup_database()
        if setup_result["status"] == "error":
            self.logger.error(f"Database setup failed: {setup_result['message']}")
            return
        self.logger.info("Database setup completed successfully.")

        server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server.setblocking(False)
        server.bind((self.host, self.port))
        server.listen(5)
        loop = asyncio.get_event_loop()
        while True:
            client, address = await loop.sock_accept(server)
            self.logger.info(f"Accepted new client connection: {address}")
            client.setblocking(False)
            self.clients.append(client)  # 新しいクライアントをリストに追加
            asyncio.create_task(self.handle_client(client, loop))

    async def handle_client(self, client, loop):
        """Handle client requests."""
        try:
            # クライアントからの接続を永続的に待機
            while True:
                data = await loop.sock_recv(client, 1024)
                if not data:
                    break  # クライアントが切断した場合に終了
                request = json.loads(data.decode())
                self.logger.debug(f"Received request: {request}")

            async with self.clients_lock:
                self.clients.append(writer)

            while True:
                try:
                    await loop.sock_sendall(client, json.dumps(response).encode())
                except (BrokenPipeError, ConnectionResetError) as e:
                    self.logger.error(f"Error sending data to client: {e}")
                    client.close()

                # メッセージが送信された場合、そのメッセージを全クライアントに送信
                if action == "add_message":
                    message_data = json.dumps(
                        {
                            "action": "new_message",
                            "message": request.get("message"),
                            "room_id": request.get("room_id"),
                            "user_id": request.get("user_id"),
                        }
                    )
                    await self.broadcast_message(message_data, loop)
                    self.logger.info(f"Broadcasted message: {message_data}")

        except Exception as e:
            self.logger.error(f"Error handling client: {e}")
            response = {"status": "error", "message": str(e)}
            await loop.sock_sendall(client, json.dumps(response).encode())

        finally:
            # クライアント切断時にリストから削除
            try:
                if client in self.clients:
                    self.clients.remove(client)
                    self.logger.info(f"Disconnected client: {client}")
            except ValueError:
                self.logger.warning(f"Client {client} was not in the client list.")
            client.close()
            self.logger.info(f"Client connection closed: {client}")

    async def route_request(self, action, request):
        """クライアントアクションを適切なメソッドにルーティングする。"""
        try:
            if action == "add_user":
                username = request.get("username")
                password = request.get("password")
                return await self.db.add_user(username, password)

            elif action == "login":
                username = request.get("username")
                password = request.get("password")
                login_result = await self.db.login(username, password)
                if login_result["status"] == "success":
                    session_id = self.create_session(login_result["user_id"])
                    return {"status": "success", "session_id": session_id}
                else:
                    return login_result

            elif action == "get_rooms_by_user":
                user_id = request.get("user_id")
                return await self.db.get_rooms_by_user(user_id)

            elif action == "get_messages_by_room":
                room_id = request.get("room_id")
                return await self.db.get_messages_by_room(room_id)

            elif action == "add_message":
                session_id = request.get("session_id")
                user_id = self.validate_session(session_id)
                if not user_id:
                    return {
                        "status": "error",
                        "message": "Session expired. Please log in again.",
                    }

                room_id = request.get("room_id")
                message = request.get("message")
                return await self.db.save_message_async(user_id, room_id, message)

            elif action == "create_room":
                session_id = request.get("session_id")
                user_id = self.validate_session(session_id)
                if not user_id:
                    return {
                        "status": "error",
                        "message": "Session expired. Please log in again.",
                    }

                room_name = request.get("room_name")
                return await self.db.create_room_async(room_name)

            elif action == "join_room":  # 入室処理を追加
                session_id = request.get("session_id")
                user_id = self.validate_session(session_id)
                if not user_id:
                    return {
                        "status": "error",
                        "message": "Session expired. Please log in again.",
                    }
                room_name = request.get("room_name")
                room_id = await self.db.create_room_async(room_name)

                # 部屋の存在と参加状態を確認
                room_exists = await self.db.check_room_exists(room_id)
                if not room_exists:
                    return {"status": "error", "message": "Room does not exist."}

                user_in_room = await self.db.is_user_in_room(user_id, room_id)
                if not user_in_room:
                    join_result = await self.db.add_user_to_room(user_id, room_id)
                    if join_result["status"] != "success":
                        return {
                            "status": "error",
                            "message": "Failed to join the room.",
                        }

                # 部屋の情報を返す
                room_info = await self.db.get_room_info(room_id)
                return {"status": "success", "room_id": room_id}

            else:
                return {"status": "error", "message": "Invalid action"}

        except Exception as e:
            self.logger.error(f"Error in action '{action}': {e}")
            return {"status": "error", "message": str(e)}

    async def broadcast_message(self, message_data, loop):
        for client in self.clients:
            try:
                await loop.sock_sendall(client, message_data.encode())
            except (BrokenPipeError, ConnectionResetError) as e:
                self.logger.error(f"Error broadcasting message to client: {e}")
                self.clients.remove(client)


if __name__ == "__main__":
    chat_server = ChatServer()
    asyncio.run(chat_server.start())
