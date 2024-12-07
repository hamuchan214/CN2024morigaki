import asyncio
import socket
import json
import time
from database import AsyncDatabase
from logging import getLogger, INFO, DEBUG, WARNING, ERROR
import colorlog
from utils import generate_session_id

# colorlog用の設定
LOG_FORMAT = "%(log_color)s%(asctime)s - %(name)s - %(levelname)s - %(message)s"
LOG_LEVEL = DEBUG
LOG_DATE_FORMAT = "%H:%M:%S"

def setup_logger():
    handler = colorlog.StreamHandler()
    formatter = colorlog.ColoredFormatter(LOG_FORMAT)
    handler.setFormatter(formatter)
    
    loger = getLogger(__name__)
    loger.addHandler(handler)
    loger.setLevel(LOG_LEVEL)
    return loger

class ChatServer:
    def __init__(self, host='127.0.0.1', port=6001):
        self.host = host
        self.port = port
        self.db = AsyncDatabase('chat.db')
        self.db.server = self #todo:直す database.pyに処理がまたがってるので修正する
        self.sessions = {}
        self.clients = []  # 接続中のクライアントを管理するリスト
        self.logger = setup_logger()

    # セッションを作成
    def create_session(self, user_id):
        session_id = generate_session_id(user_id)
        exception_time = time.time() + 3600
        self.sessions[session_id] = (user_id, exception_time)
        print(f"Session created: {self.sessions}")
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

        server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server_socket.bind((self.host, self.port))
        server_socket.listen(5)
        self.logger.info(f"Server listening on {self.host}:{self.port}")

        while True:
            client_socket, client_address = await asyncio.get_running_loop().run_in_executor(
                None, server_socket.accept
            )
            print(f"Connection from {client_address}")
            # クライアントを管理するリストに追加
            self.clients.append(client_socket)
            asyncio.create_task(self.handle_client(client_socket))

    async def handle_client(self, client_socket):
        """Handle client requests."""
        try:
            data = await asyncio.get_running_loop().run_in_executor(None, client_socket.recv, 1024)
            if data:
                request = json.loads(data.decode())
                print(f"Received request: {request}")

                action = request.get('action')
                response = await self.route_request(action, request)

                # クライアントへのレスポンス送信
                client_socket.sendall(json.dumps(response).encode())

                # メッセージが送信された場合、そのメッセージを全クライアントに送信
                if action == 'add_message':
                    message_data = json.dumps({
                        'action': 'new_message',
                        'message': request.get('message'),
                        'room_id': request.get('room_id'),
                        'user_id': request.get('user_id')
                    })
                    await self.broadcast_message(message_data)
                
        except Exception as e:
            print(f"Error handling client: {e}")
            response = {"status": "error", "message": str(e)}
            client_socket.sendall(json.dumps(response).encode())
        finally:
            # クライアント切断時にリストから削除
            self.clients.remove(client_socket)
            client_socket.close()

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
                user_id = login_result["user_id"]
                session_id = self.create_session(user_id)
                return {"status": "success", "session_id": session_id}
            else:
                return login_result
        
        elif action == 'get_rooms_by_user':
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
                return {"status": "success", "room_id": create_room_result["room_id"]}
            else:
                return {"status": "error", "message": create_room_result["message"]}

        else:
            return {"status": "error", "message": "Invalid action"}

    async def broadcast_message(self, message):
        """接続中の全クライアントにメッセージをブロードキャスト"""
        for client_socket in self.clients:
            try:
                client_socket.sendall(message.encode())
            except Exception as e:
                print(f"Error broadcasting message to client: {e}")
                self.clients.remove(client_socket)  # エラーが発生したクライアントはリストから削除
                client_socket.close()

if __name__ == "__main__":
    chat_server = ChatServer()
    asyncio.run(chat_server.start())