import sqlite3
import asyncio
import json
import socket
from functools import partial
import hashlib
import time


class AsyncDatabase:
    def __init__(self, db_name):
        self.db_name = db_name
        self.connection = sqlite3.connect(db_name, check_same_thread=False)
        self.connection.row_factory = sqlite3.Row  # Allows accessing columns by name

    async def execute_async(self, query):
        """Execute a write operation asynchronously."""
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(None, self._execute, query)

    async def query_async(self, query):
        """Execute a read operation asynchronously."""
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(None, self._query, query)

    def _execute(self, query):
        """Internal synchronous execution of a write operation."""
        try:
            cursor = self.connection.cursor()
            cursor.execute(query)
            self.connection.commit()
            cursor.close()
            return {"status": "success"}
        except Exception as e:
            return {"status": "error", "message": str(e)}

    def _query(self, query):
        """Internal synchronous execution of a read operation."""
        try:
            cursor = self.connection.cursor()
            cursor.execute(query)
            rows = cursor.fetchall()
            cursor.close()
            return {"status": "success", "data": [dict(row) for row in rows]}
        except Exception as e:
            return {"status": "error", "message": str(e)}

    async def setup_database(self):
        """Initialize database schema."""
        queries = [
            """CREATE TABLE IF NOT EXISTS User (
                user_id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL UNIQUE,
                password TEXT NOT NULL,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            );""",
            """CREATE TABLE IF NOT EXISTS Room (
                room_id INTEGER PRIMARY KEY AUTOINCREMENT,
                room_name TEXT NOT NULL UNIQUE,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            );""",
            """CREATE TABLE IF NOT EXISTS Message (
                message_id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                room_id INTEGER NOT NULL,
                message TEXT NOT NULL,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(user_id) REFERENCES User(user_id),
                FOREIGN KEY(room_id) REFERENCES Room(room_id)
            );""",
            """CREATE TABLE IF NOT EXISTS RoomUser (
                user_id INTEGER NOT NULL,
                room_id INTEGER NOT NULL,
                last_read_at DATETIME,
                PRIMARY KEY(user_id, room_id),
                FOREIGN KEY(user_id) REFERENCES User(user_id),
                FOREIGN KEY(room_id) REFERENCES Room(room_id)
            );"""
        ]
        for query in queries:
            result = await self.execute_async(query)
            if result["status"] == "error":
                return result
        return {"status": "success"}

    async def login(self, username, password):
        """Login a user asynchronously."""
        query = "SELECT id, password FROM users WHERE username = ?"
        
        def authenticate():
            try:
                cursor = self.connection.cursor()
                cursor.execute(query, (username,))
                row = cursor.fetchone()
                cursor.close()
                if not row:
                    return {"status": "error", "message": "Invalid username or password"} 
                
                user_id, stored_password = row
                hashed_password = hashlib.sha256(password.encode()).hexdigest()
                if hashed_password == stored_password:
                    session_id = self.server.create_session(user_id)
                    return {"status": "success", "session_id": session_id}
                else:
                    return {"status": "error", "message": "Invalid username or password"}
            except Exception as e:
                return {"status": "error", "message": str(e)}

        return await asyncio.get_running_loop().run_in_executor(self.executor, authenticate)

    async def add_user(self, username, password):
        """Add a new user asynchronously."""
        query = f"INSERT INTO User (username, password) VALUES ('{username}', '{password}');"
        loop = asyncio.get_running_loop()

        def execute_and_fetch_lastrowid():
            try:
                cursor = self.connection.cursor()
                cursor.execute(query)
                self.connection.commit()
                user_id = cursor.lastrowid  # Fetch the last inserted row ID
                cursor.close()
                return {"status": "success", "user_id": user_id}
            except sqlite3.IntegrityError:
                return {"status": "error", "message": "Username already exists"}
            except Exception as e:
                return {"status": "error", "message": str(e)}

        return await loop.run_in_executor(None, execute_and_fetch_lastrowid)

    def update_user_async(self, user_id, new_password, callback):
        query = f"UPDATE User SET password = '{new_password}' WHERE user_id = {user_id};"
        self.execute_async(query, callback)

    def delete_user_async(self, user_id, callback):
        query = f"DELETE FROM User WHERE user_id = {user_id};"
        self.execute_async(query, callback)

    def get_user_async(self, user_id, callback):
        query = f"SELECT username, password FROM User WHERE user_id = {user_id};"
        self.query_async(query, callback)

    def get_rooms_by_user_async(self, user_id, callback):
        query = f"""SELECT Room.room_id, Room.room_name, Room.created_at
                    FROM RoomUser
                    INNER JOIN Room ON RoomUser.room_id = Room.room_id
                    WHERE RoomUser.user_id = {user_id};"""
        self.query_async(query, callback)

    def get_messages_by_room_async(self, room_id, callback):
        query = f"""SELECT Message.message_id, User.username, Message.message, Message.timestamp
                    FROM Message
                    INNER JOIN User ON Message.user_id = User.user_id
                    WHERE Message.room_id = {room_id}
                    ORDER BY Message.timestamp ASC;"""
        self.query_async(query, callback)

    def get_room_members_async(self, room_id, callback):
        query = f"""SELECT User.user_id, User.username
                    FROM RoomUser
                    INNER JOIN User ON RoomUser.user_id = User.user_id
                    WHERE RoomUser.room_id = {room_id};"""
        self.query_async(query, callback)

    def create_room_async(self, room_name, callback):
        query = f"INSERT INTO Room (room_name) VALUES ('{room_name}');"
        self.execute_async(query, callback)

    def delete_room_async(self, room_id, callback):
        query = f"DELETE FROM Room WHERE room_id = {room_id};"
        self.execute_async(query, callback)

    def send_message_async(self, user_id, room_id, message, callback):
        query = f"""INSERT INTO Message (user_id, room_id, message)
                    VALUES ({user_id}, {room_id}, '{message}');"""
        self.execute_async(query, callback)

    def add_user_to_room_async(self, user_id, room_id, callback):
        query = f"""INSERT OR IGNORE INTO RoomUser (user_id, room_id, last_read_at)
                    VALUES ({user_id}, {room_id}, datetime('now'));"""
        self.execute_async(query, callback)

    def remove_user_from_room_async(self, user_id, room_id, callback):
        query = f"DELETE FROM RoomUser WHERE user_id = {user_id} AND room_id = {room_id};"
        self.execute_async(query, callback)


class ChatServer:
    def __init__(self, host='127.0.0.1', port=6001):
        self.host = host
        self.port = port
        self.db = AsyncDatabase('chat.db')
        self.loop = asyncio.get_event_loop()
        self.sessions = {}
        
    def create_session(self, user_id):
        session_id = hashlib.sha256(f"{user_id}{time.time()}".encode()).hexdigest()
        self.sessions[session_id] = user_id
        return session_id

    async def start(self):
        """Start the server."""
        setup_result = await self.db.setup_database()
        if setup_result["status"] == "error":
            print(f"Database setup failed: {setup_result['message']}")
            return
        print("Database setup completed successfully.")

        server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server_socket.bind((self.host, self.port))
        server_socket.listen(5)
        print(f"Server listening on {self.host}:{self.port}")

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
        else:
            return {"status": "error", "message": "Invalid action"}


if __name__ == "__main__":
    server = ChatServer()
    try:
        asyncio.run(server.start())
    except KeyboardInterrupt:
        print("Server shutting down.")