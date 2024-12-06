import asyncio
import socket
import json
import time
from database import AsyncDatabase
from logging import getLogger, DEBUG
import colorlog
from utils import generate_session_id

# Logger setup
LOG_FORMAT = "%(log_color)s%(asctime)s - %(name)s - %(levelname)s - %(message)s"
LOG_LEVEL = DEBUG

def setup_logger():
    handler = colorlog.StreamHandler()
    formatter = colorlog.ColoredFormatter(LOG_FORMAT)
    handler.setFormatter(formatter)
    
    logger = getLogger(__name__)
    logger.addHandler(handler)
    logger.setLevel(LOG_LEVEL)
    return logger

# Parameter validation decorator
def extract_request_params(required_params):
    """Decorator to extract and validate parameters from the request."""
    def decorator(func):
        async def wrapper(self, request):
            missing_params = [p for p in required_params if p not in request]
            if missing_params:
                return {"status": "error", "message": f"Missing parameters: {missing_params}"}
            return await func(self, **{p: request[p] for p in required_params})
        return wrapper
    return decorator

# Session validation decorator
def require_valid_session(func):
    """Decorator to validate session and inject user_id."""
    async def wrapper(self, session_id, **kwargs):
        user_id = self.validate_session(session_id)
        if not user_id:
            return {"status": "error", "message": "Invalid or expired session"}
        return await func(self, user_id=user_id, **kwargs)
    return wrapper

class ChatServer:
    def __init__(self, host='127.0.0.1', port=6001):
        self.host = host
        self.port = port
        self.db = AsyncDatabase('chat.db')
        self.sessions = {}
        self.room_users = {}
        self.logger = setup_logger()

    def create_session(self, user_id):
        """Create a new session ID."""
        session_id = generate_session_id(user_id)
        expiration_time = time.time() + 3600
        self.sessions[session_id] = (user_id, expiration_time)
        self.logger.debug(f"Session created: {self.sessions}")
        return session_id

    def validate_session(self, session_id):
        """Validate the given session ID."""
        session = self.sessions.get(session_id)
        if session:
            user_id, expiration_time = session
            if time.time() < expiration_time:
                return user_id
            else:
                del self.sessions[session_id]
        return None

    async def initialize_user_rooms(self, user_id, client_socket):
        """
        Initialize user rooms.
        """
        rooms = await self.db.get_rooms_by_user_async(user_id)
        for room_id in rooms:
            if room_id not in self.room_users:
                self.room_users[room_id] = []
            self.room_users[room_id].append(client_socket)
            
    async def handle_user_disconnect(self, client_socket):
        """
        Remove a disconnected user's socket from all rooms.
        """
        for room_id, sockets in list(self.room_users.items()):
            if client_socket in sockets:
                sockets.remove(client_socket)
                if not sockets:  # ルームが空になったら削除
                    del self.room_users[room_id]
                    
    async def broadcast_message_to_room(self, room_id, message, sender_socket):
        """
        Broadcast a message to all members of a room except the sender.
        """
        if room_id in self.room_users:
            for user_socket in self.room_users[room_id]:
                if user_socket != sender_socket:
                    try:
                        await asyncio.get_running_loop().run_in_executor(
                            None, user_socket.sendall, message.encode()
                        )
                    except Exception as e:
                        self.logger.error(f"Failed to send message to room {room_id}: {e}")

    async def start(self):
        """Start the server."""
        setup_result = await self.db.setup_database()
        if setup_result["status"] == "error":
            self.logger.error(f"Database setup failed: {setup_result['message']}")
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
            self.logger.info(f"Connection from {client_address}")
            asyncio.create_task(self.handle_client(client_socket))

    async def handle_client(self, client_socket):
        """
        Handle client requests.
        """
        try:
            data = await asyncio.get_running_loop().run_in_executor(None, client_socket.recv, 1024)
            if data:
                request = json.loads(data.decode())
                self.logger.debug(f"Received request: {request}")

                action = request.get('action')
                response = await self.route_request(action, request, client_socket)

                client_socket.sendall(json.dumps(response).encode())
        except Exception as e:
            self.logger.error(f"Error handling client: {e}")
            response = {"status": "error", "message": str(e)}
            client_socket.sendall(json.dumps(response).encode())
        finally:
            await self.handle_user_disconnect(client_socket)
            client_socket.close()

    async def route_request(self, action, request, client_socket):
        """Route client actions to the appropriate handlers."""
        actions = {
            'add_user': self.add_user_handler,
            'login': self.login_handler,
            'get_rooms_by_user': self.get_rooms_by_user_handler,
            'get_messages_by_room': self.get_messages_by_room_handler,
            'add_message': self.add_message_handler,
            'create_room': self.create_room_handler,
        }

        handler = actions.get(action)
        if not handler:
            return {"status": "error", "message": "Invalid action"}
        return await handler(request, client_socket)

    # Action Handlers
    @extract_request_params(['username', 'password'])
    async def add_user_handler(self, username, password):
        return await self.db.add_user(username, password)

    @extract_request_params(['username', 'password'])
    async def login_handler(self, username, password):
        login_result = await self.db.login(username, password)
        if login_result["status"] == "success":
            user_id = login_result["user_id"]
            session_id = self.create_session(user_id)
            return {"status": "success", "session_id": session_id}
        else:
            return login_result

    @extract_request_params(['user_id'])
    async def get_rooms_by_user_handler(self, user_id):
        return await self.db.get_rooms_by_user(user_id)

    @extract_request_params(['room_id'])
    async def get_messages_by_room_handler(self, room_id):
        return await self.db.get_messages_by_room(room_id)

    @extract_request_params(['session_id', 'room_id', 'message'])
    @require_valid_session
    async def add_message_handler(self, user_id, room_id, message):
        save_result = await self.db.save_message_async(user_id, room_id, message)
        if save_result["status"] == "success":
            return {"status": "success", "message_id": save_result["message_id"]}
        else:
            return {"status": "error", "message": save_result["message"]}

    @extract_request_params(['session_id', 'room_name'])
    @require_valid_session
    async def create_room_handler(self, user_id, room_name):
        create_room_result = await self.db.create_room_async(room_name)
        if create_room_result["status"] == "success":
            return {"status": "success", "room_id": create_room_result["room_id"]}
        else:
            return {"status": "error", "message": create_room_result["message"]}
