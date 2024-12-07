import asyncio
import socket
import json
import time
from database import AsyncDatabase
from logging import getLogger, DEBUG, ERROR, INFO
import colorlog
from utils import generate_session_id
from typing import Callable

# Logger setup
LOG_FORMAT = "%(log_color)s%(asctime)s - %(name)s - %(levelname)s - %(message)s"
LOG_LEVEL = DEBUG

def setup_logger() -> getLogger:
    handler = colorlog.StreamHandler()
    formatter = colorlog.ColoredFormatter(LOG_FORMAT)
    handler.setFormatter(formatter)
    
    logger = getLogger(__name__)
    logger.addHandler(handler)
    logger.setLevel(LOG_LEVEL)
    return logger

import json
from typing import Callable

def extract_request_params(required_params: list[str]) -> Callable:
    """Decorator to extract and validate parameters from the JSON request."""
    def decorator(func: Callable):
        async def wrapper(self, request: dict, *args, **kwargs):
            self.logger.debug(f"Validating parameters for action: {func.__name__}")
            
            # Check for missing required parameters
            missing_params = [p for p in required_params if p not in request or not request[p]]
            if missing_params:
                self.logger.debug(f"Missing parameters: {missing_params}")
                return {"status": "error", "message": f"Missing parameters: {missing_params}"}
            
            # Filtered params to pass as kwargs
            filtered_kwargs = {param: request[param] for param in required_params}
            self.logger.debug(f"Extracted parameters: {filtered_kwargs}")
            return await func(self, *args, **filtered_kwargs)
        return wrapper
    return decorator

def require_valid_session(func: Callable) -> Callable:
    """Decorator to validate session and inject user_id."""
    async def wrapper(self, session_id: str, **kwargs):
        user_id = self.validate_session(session_id)
        if not user_id:
            self.logger.warning(f"Invalid or expired session: {session_id}")
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
        self.socket_user_map = {}  # ソケットとユーザーIDの紐付け
        self.logger = setup_logger()

    def create_session(self, user_id: str) -> str:
        """Create a new session ID."""
        session_id = generate_session_id(user_id)
        expiration_time = time.time() + 3600
        self.sessions[session_id] = (user_id, expiration_time)
        self.logger.info(f"Session created for user {user_id}: {session_id}")
        return session_id

    def validate_session(self, session_id: str) -> str | None:
        """Validate the given session ID."""
        session = self.sessions.get(session_id)
        if session and time.time() < session[1]:
            self.logger.debug(f"Session {session_id} is valid for user {session[0]}")
            return session[0]
        self.sessions.pop(session_id, None)
        self.logger.warning(f"Session {session_id} is invalid or expired")
        return None

    async def initialize_user_rooms(self, user_id: str, client_socket: socket.socket):
        """Initialize user rooms."""
        rooms = await self.db.get_rooms_by_user_async(user_id)
        for room_id in rooms:
            self.room_users.setdefault(room_id, []).append(client_socket)
        self.logger.info(f"Initialized rooms for user {user_id}: {rooms}")
        
        # ユーザーIDとソケットを紐付ける
        self.socket_user_map[client_socket] = user_id
        self.logger.info(f"Socket {client_socket.getpeername()} mapped to user {user_id}")

    async def handle_user_disconnect(self, client_socket: socket.socket):
        """Remove a disconnected user's socket from all rooms and map."""
        user_id = self.socket_user_map.get(client_socket)
        if user_id:
            self.logger.info(f"User {user_id} disconnected.")
            # ソケットを紐解いて部屋から削除
            for room_id, sockets in list(self.room_users.items()):
                if client_socket in sockets:
                    sockets.remove(client_socket)
                    if not sockets:
                        del self.room_users[room_id]
            del self.socket_user_map[client_socket]
            self.logger.info(f"Socket {client_socket.getpeername()} unmapped from user {user_id}")

    async def broadcast_message_to_room(self, room_id: str, message: str, sender_socket: socket.socket):
        """Broadcast a message to all members of a room except the sender."""
        for user_socket in self.room_users.get(room_id, []):
            if user_socket != sender_socket:
                await self._send_message(user_socket, message)
        self.logger.info(f"Broadcast message to room {room_id}: {message[:20]}...")

    async def _send_message(self, client_socket: socket.socket, message: str):
        """Helper method to send messages asynchronously."""
        try:
            if isinstance(message, dict):
                message = json.dumps(message)

            # Convert message to bytes
            if isinstance(message, str):
                message = message.encode("utf-8")

            await asyncio.get_running_loop().sock_sendall(client_socket, message)
            self.logger.debug(f"Message sent: {message.decode('utf-8')}")
        except Exception as e:
            self.logger.error(f"Failed to send message to {client_socket.getpeername()}: {e}")

    async def start(self):
        """Start the server."""
        setup_result = await self.db.setup_database()
        if setup_result.get("status") == "error":
            self.logger.error(f"Database setup failed: {setup_result['message']}")
            return
        self.logger.info("Database setup completed successfully.")

        server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server_socket.bind((self.host, self.port))
        server_socket.listen(5)
        self.logger.info(f"Server listening on {self.host}:{self.port}")

        while True:
            client_socket, client_address = await asyncio.get_running_loop().run_in_executor(None, server_socket.accept)
            self.logger.info(f"Connection from {client_address}")
            asyncio.create_task(self.handle_client(client_socket))

    async def handle_client(self, client_socket):
        """Handle client requests."""
        try:
            while True:  # Keep the connection alive
                self.logger.debug("Waiting to receive data from client.")
                data = await asyncio.get_running_loop().run_in_executor(None, client_socket.recv, 1024)
                
                if not data:
                    self.logger.info(f"Client {client_socket.getpeername()} disconnected")
                    break  # Disconnect if no data

                request = json.loads(data.decode())
                self.logger.debug(f"Decoded request: {request}")

                session_id = request.get('session_id')
                if not session_id:
                    # セッションIDがない場合は、ユーザー登録やログイン処理などを処理できるようにする
                    action = request.get('action')
                    if action and action in ['add_user', 'login']:
                        response = await self.route_request(action, request, client_socket)
                        await self._send_message(client_socket, response)
                        continue  # セッションIDがない場合、ログインやユーザー登録を先に処理
                    else:
                        await self._send_message(client_socket, {"status": "error", "message": "Missing session_id"})
                        continue  # セッションIDがない場合は、エラーメッセージを返す

                # セッションIDがある場合にのみセッションを検証
                action = request.get('action')
                if action:
                    response = await self.route_request(action, request, client_socket)
                    await self._send_message(client_socket, response)

        except Exception as e:
            self.logger.error(f"Error handling client {client_socket.getpeername()}: {e}")
            await self._send_message(client_socket, {"status": "error", "message": str(e)})
        finally:
            self.logger.debug(f"Client {client_socket.getpeername()} handling complete.")

    async def route_request(self, action: str, request: dict, client_socket: socket.socket):
        """Route client actions to the appropriate handlers."""
        actions = {
            'add_user': self.add_user_handler,
            'login': self.login_handler,
            'get_rooms_by_user': self.get_rooms_by_user_handler,
            'get_messages_by_room': self.get_messages_by_room_handler,
            'add_message': self.add_message_handler,
            'create_room': self.create_room_handler,
            'get_room_members': self.get_room_members_handler,
            'join_room': self.add_user_to_room_handler,
        }

        handler = actions.get(action)
        if not handler:
            self.logger.warning(f"Invalid action received: {action}")
            return {"status": "error", "message": "Invalid action"}
        
        try:
            # Extract parameters and handle request
            response = await handler(request)
            return response
        except Exception as e:
            self.logger.error(f"Error in handler for action '{action}': {e}")
            return {"status": "error", "message": str(e)}

    # Action Handlers
    @extract_request_params(['username', 'password'])
    async def add_user_handler(self, username: str, password: str):
        result = await self.db.add_user(username, password)
        if result["status"] == "success":
            self.logger.info(f"User '{username}' added successfully.")
        else:
            self.logger.warning(f"Failed to add user '{username}': {result.get('message')}")
        return result

    @extract_request_params(['username', 'password'])
    async def login_handler(self, username: str, password: str):
        login_result = await self.db.login(username, password)
        if login_result["status"] == "success":
            self.logger.info(f"User '{username}' logged in successfully.")
        else:
            self.logger.warning(f"Failed login for user '{username}': {login_result.get('message')}")
        return login_result

    @extract_request_params(['user_id'])
    async def get_rooms_by_user_handler(self, user_id: str):
        result = await self.db.get_rooms_by_user(user_id)
        if result:
            self.logger.info(f"Fetched rooms for user '{user_id}' successfully.")
        else:
            self.logger.warning(f"Failed to fetch rooms for user '{user_id}'.")
        return result

    @extract_request_params(['room_id'])
    async def get_messages_by_room_handler(self, room_id: str):
        result = await self.db.get_messages_by_room(room_id)
        if result:
            self.logger.info(f"Fetched messages for room '{room_id}' successfully.")
        else:
            self.logger.warning(f"Failed to fetch messages for room '{room_id}'.")
        return result

    @extract_request_params(['session_id', 'room_id', 'message'])
    @require_valid_session
    async def add_message_handler(self, user_id: str, room_id: str, message: str):
        save_result = await self.db.save_message_async(user_id, room_id, message)
        if save_result["status"] == "success":
            self.logger.info(f"Message added to room '{room_id}' by user '{user_id}' successfully.")
        else:
            self.logger.warning(f"Failed to add message to room '{room_id}': {save_result.get('message')}")
        return save_result

    @extract_request_params(['session_id', 'room_name'])
    @require_valid_session
    async def create_room_handler(self, user_id: str, room_name: str):
        create_room_result = await self.db.create_room_async(room_name)
        if create_room_result["status"] == "success":
            self.logger.info(f"Room '{room_name}' created successfully by user '{user_id}'.")
        else:
            self.logger.warning(f"Failed to create room '{room_name}' for user '{user_id}': {create_room_result.get('message')}")
        return create_room_result

    @extract_request_params(['room_id'])
    async def get_room_members_handler(self, room_id: str):
        result = await self.db.get_room_members_async(room_id)
        if result["status"] == "success":
            self.logger.info(f"Fetched members for room '{room_id}' successfully.")
        else:
            self.logger.warning(f"Failed to fetch members for room '{room_id}': {result.get('message')}")
        return result

    @extract_request_params(['room_id', 'user_id'])
    async def add_user_to_room_handler(self, room_id: str, user_id: str):
        result = await self.db.add_user_to_room_async(room_id, user_id)
        if result["status"] == "success":
            self.logger.info(f"User '{user_id}' added to room '{room_id}' successfully.")
        else:
            self.logger.warning(f"Failed to add user '{user_id}' to room '{room_id}': {result.get('message')}")
        return result