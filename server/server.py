import asyncio
import json
import time
from database import AsyncDatabase
from logging import getLogger, DEBUG
import colorlog
from utils import generate_session_id
import socket

# colorlog用の設定
LOG_FORMAT = "%(log_color)s%(asctime)s - %(name)s - %(levelname)s - %(message)s"
LOG_LEVEL = DEBUG
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
    def __init__(self, host='127.0.0.1', port=6001):
        self.host = host
        self.port = port
        self.db = AsyncDatabase('chat.db')
        self.db.server = self  # todo: database.pyに処理がまたがっているので修正する
        self.sessions = {}
        self.clients = []  # 接続中のクライアントを管理するリスト
        self.logger = setup_logger()

    # セッションを作成
    def create_session(self, user_id):
        session_id = generate_session_id(user_id)
        exception_time = time.time() + 3600
        self.sessions[session_id] = (user_id, exception_time)
        self.logger.debug(f"Session created: {self.sessions}")
        return session_id
    
    # セッションの有効期限を確認
    def validate_session(self, session_id):
        """
        Validate the given session ID.
        param session_id: セッションID
        return: セッションが有効ならユーザーIDを返し、無効なら None を返す
        """
        session = self.sessions.get(session_id)
        if session:
            user_id, exception_time = session
            if time.time() < exception_time:
                return user_id
            else:
                del self.sessions[session_id]
        return None

    async def start(self):
        """Start the server."""
        setup_result = await self.db.setup_database()
        if setup_result["status"] == "error":
            self.logger.info(f"Database setup failed: {setup_result['message']}")
            return
        self.logger.warning("Database setup completed successfully.")

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

                action = request.get('action')
                response = await self.route_request(action, request)

                # クライアントへのレスポンス送信
                try:
                    await loop.sock_sendall(client, json.dumps(response).encode())
                except (BrokenPipeError, ConnectionResetError) as e:
                    self.logger.error(f"Error sending data to client: {e}")
                    client.close()

                # メッセージが送信された場合、そのメッセージを全クライアントに送信
                if action == 'add_message':
                    message_data = json.dumps({
                        'action': 'new_message',
                        'message': request.get('message'),
                        'room_id': request.get('room_id'),
                        'user_id': request.get('user_id')
                    })
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
        """Route client actions to the appropriate database methods."""
        if action == 'add_user':
            username = request.get('username')
            password = request.get('password')
            return await self.db.add_user(username, password)
        
        elif action == 'login':
            username = request.get('username')
            password = request.get('password')
            login_result = await self.db.login(username, password)
        
            if login_result["status"] == "success":
                self.logger.info(f"User {username} logged in.")
                user_id = login_result["user_id"]
                session_id = self.create_session(user_id)
                return {"status": "success", "session_id": session_id}
            else:
                return login_result
        
        elif action == 'get_rooms_by_user':
            self.logger.debug("get_rooms_by_user")
            user_id = request.get('user_id')
            return await self.db.get_rooms_by_user(user_id)
        
        elif action == 'get_messages_by_room':
            room_id = request.get('room_id')
            return await self.db.get_messages_by_room(room_id)
        
        elif action == 'add_message':
            session_id = request.get('session_id')
            room_id = request.get('room_id')
            message = request.get('message')

            user_id = self.validate_session(session_id)
            if not user_id:
                return {"status": "error", "message": "Invalid or expired session"}

            save_result = await self.db.save_message_async(user_id, room_id, message)

            if save_result["status"] == "success":
                self.logger.info(f"Message saved with ID: {save_result['message_id']}")
                return {"status": "success", "message_id": save_result["message_id"]}
            else:
                return {"status": "error", "message": save_result["message"]}

        elif action == 'create_room':
            session_id = request.get('session_id')
            room_name = request.get('room_name')

            user_id = self.validate_session(session_id)
            if not user_id:
                return {"status": "error", "message": "Invalid or expired session"}

            create_room_result = await self.db.create_room_async(room_name)

            if create_room_result["status"] == "success":
                self.logger.info(f"Room created with ID: {create_room_result['room_id']}")
                return {"status": "success", "room_id": create_room_result["room_id"]}
            else:
                return {"status": "error", "message": create_room_result["message"]}

        else:
            return {"status": "error", "message": "Invalid action"}

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
