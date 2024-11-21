import asyncio
import socket
import json
import time
from database import AsyncDatabase
from logging import getLogger, basicConfig, INFO
from utils import generate_session_id

#ログの設定
basicConfig(level=INFO, format = "%(asctime)s %(levelname)s %(message)s")

class ChatServer:
    def __init__(self, host='127.0.0.1', port=6001):
        self.host = host
        self.port = port
        self.db = AsyncDatabase('chat.db')
        self.db.server = self
        self.sessions = {}
        self.logger = getLogger(__name__)

    #セッションを作成
    def create_session(self, user_id):
        session_id = generate_session_id(user_id)
        exception_time = time.time() + 3600
        self.sessions[session_id] = (user_id, exception_time)
        print(f"Session created: {self.sessions}")
        return session_id
    
    #セッションの有効期限を確認
    def validate_session(self, session_id):
        ###
        #alidate the given session ID.
        #param session_id: セッションID
        #return: セッションが有効ならユーザーIDを返し、無効なら None を返す
        ###
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
        self.logger.info("Database setup completed successfully.")

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

                client_socket.sendall(json.dumps(response).encode())
        except Exception as e:
            print(f"Error handling client: {e}")
            response = {"status": "error", "message": str(e)}
            client_socket.sendall(json.dumps(response).encode())
        finally:
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
        
        else:
            return {"status": "error", "message": "Invalid action"}
