import sqlite3
import asyncio
import hashlib
from logging import getLogger, DEBUG
import colorlog

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

class AsyncDatabase:
    def __init__(self, db_name):
        self.db_name = db_name
        self.connection = sqlite3.connect(db_name, check_same_thread=False)
        self.connection.row_factory = sqlite3.Row  # Allows accessing columns by name
        self.logger = setup_logger()

    async def execute_async(self, query, params=None):
        """Execute a query asynchronously using cursor."""
        loop = asyncio.get_running_loop()

        def execute_query():
            try:
                cursor = self.connection.cursor()
                cursor.execute(query, params or ())
                self.connection.commit()
                cursor.close()
                return {"status": "success"}
            except Exception as e:
                return {"status": "error", "message": str(e)}

        # Run the database operation asynchronously
        return await loop.run_in_executor(None, execute_query)

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
        query = "SELECT user_id, password FROM User WHERE username = ?"
        
        def authenticate():
            try:
                cursor = self.connection.cursor()
                cursor.execute(query, (username,))
                row = cursor.fetchone()
                cursor.close()

                print(f"Database returned row: {row}")  # Debugging output

                if not row:
                    return {"status": "error", "message": "Invalid username or password"} 
                
                user_id, stored_password = row
                print(f"user_id: {user_id}, stored_password: {stored_password}")  # Debugging output

                hashed_password = hashlib.sha256(password.encode()).hexdigest()
                print(f"hashed_password: {hashed_password}")  # Debugging output

                if hashed_password == stored_password:
                    return {"status": "success", "user_id": user_id}
                else:
                    return {"status": "error", "message": "Invalid username or password"}
            except Exception as e:
                return {"status": "error", "message": str(e)}

        return await asyncio.get_running_loop().run_in_executor(None, authenticate)

    async def add_user(self, username, password):
        """Add a new user asynchronously."""
        hashed_password = hashlib.sha256(password.encode()).hexdigest()
        query = f"INSERT INTO User (username, password) VALUES (?, ?)"
        params = (username, hashed_password)
        
        loop = asyncio.get_running_loop()

        def execute_and_fetch_lastrowid():
            try:
                cursor = self.connection.cursor()
                cursor.execute(query, params)
                self.connection.commit()
                user_id = cursor.lastrowid  # Fetch the last inserted row ID
                cursor.close()
                self.logger.info(f"New user added with ID: {user_id}")
                return {"status": "success", "user_id": user_id}
            except sqlite3.IntegrityError:
                self.logger.error("Username:{user_name} already exists")
                return {"status": "error", "message": "Username already exists"}
            except Exception as e:
                self.logger.error(f"Error adding user: {e}")
                return {"status": "error", "message": str(e)}

        return await loop.run_in_executor(None, execute_and_fetch_lastrowid)

    async def update_user_async(self, user_id, new_password):
        """Update user's password asynchronously."""
        hashed_password = hashlib.sha256(new_password.encode()).hexdigest()
        query = "UPDATE User SET password = ? WHERE user_id = ?"
        params = (hashed_password, user_id)
        try:
            cursor = self.connection.cursor()
            cursor.execute(query, params)
            self.connection.commit()
            cursor.close()
            return {"status": "success"}
        except Exception as e:
            return {"status": "error", "message": str(e)}

    async def save_message_async(self, user_id, room_id, message):
        """Save a new message asynchronously."""
        query = """
            INSERT INTO Message (user_id, room_id, message)
            VALUES (?, ?, ?);
        """
        params = (user_id, room_id, message)

        def execute_and_return_message_id():
            try:
                cursor = self.connection.cursor()
                cursor.execute(query, params)
                self.connection.commit()
                message_id = cursor.lastrowid
                cursor.close()
                return {"status": "success", "message_id": message_id}
            except sqlite3.IntegrityError:
                return {"status": "error", "message": "Invalid user_id or room_id"}
            except Exception as e:
                return {"status": "error", "message": str(e)}

        return await asyncio.get_running_loop().run_in_executor(None, execute_and_return_message_id)

    async def get_rooms_by_user(self, user_id):
        """Get a list of rooms the user belongs to."""
        query = """SELECT Room.room_id, Room.room_name, Room.created_at
                   FROM RoomUser
                   INNER JOIN Room ON RoomUser.room_id = Room.room_id
                   WHERE RoomUser.user_id = ?;"""
        try:
            cursor = self.connection.cursor()
            cursor.execute(query, (user_id,))
            rooms = cursor.fetchall()
            cursor.close()
            room_list = [{"room_id": room[0], "room_name": room[1], "created_at": room[2]} for room in rooms]
            return {"status": "success", "rooms": room_list}
        except Exception as e:
            return {"status": "error", "message": str(e)}

    async def create_room_async(self, room_name):
        """Create a new chat room asynchronously."""
        query = "INSERT INTO Room (room_name) VALUES (?)"
        params = (room_name,)

        def execute_and_return_room_id():
            try:
                cursor = self.connection.cursor()
                cursor.execute(query, params)
                self.connection.commit()
                room_id = cursor.lastrowid
                cursor.close()
                return {"status": "success", "room_id": room_id}
            except sqlite3.IntegrityError:
                return {"status": "error", "message": "Room name already exists"}
            except Exception as e:
                return {"status": "error", "message": str(e)}

        return await asyncio.get_running_loop().run_in_executor(None, execute_and_return_room_id)

    async def get_messages_by_room(self, room_id):
        """Retrieve all messages for a specific room asynchronously."""
        query = "SELECT message_id, user_id, message, timestamp FROM Message WHERE room_id = ? ORDER BY timestamp ASC"
        
        try:
            cursor = self.connection.cursor()
            cursor.execute(query, (room_id,))
            messages = [{"message_id": row[0], "user_id": row[1], "message": row[2], "timestamp": row[3]} for row in cursor.fetchall()]
            cursor.close()
            return {"status": "success", "messages": messages}
        except Exception as e:
            return {"status": "error", "message": str(e)}
        
    async def add_user_to_room(self, user_id, room_id):
        """Add a user to a specific room."""
        query = """
            INSERT OR IGNORE INTO RoomUser (user_id, room_id, last_read_at)
            VALUES (?, ?, CURRENT_TIMESTAMP);
        """
        params = (user_id, room_id)

        def execute_and_return_status():
            try:
                cursor = self.connection.cursor()
                cursor.execute(query, params)
                self.connection.commit()
                cursor.close()
                return {"status": "success"}
            except Exception as e:
                return {"status": "error", "message": str(e)}

        return await asyncio.get_running_loop().run_in_executor(None, execute_and_return_status)

    async def remove_user_from_room(self, user_id, room_id):
        """Remove a user from a specific room."""
        query = "DELETE FROM RoomUser WHERE user_id = ? AND room_id = ?"
        params = (user_id, room_id)

        def execute_and_return_status():
            try:
                cursor = self.connection.cursor()
                cursor.execute(query, params)
                self.connection.commit()
                cursor.close()
                return {"status": "success"}
            except Exception as e:
                return {"status": "error", "message": str(e)}

        return await asyncio.get_running_loop().run_in_executor(None, execute_and_return_status)

    async def get_users_in_room(self, room_id):
        """Retrieve all users in a specific room."""
        query = """
            SELECT user_id FROM RoomUser WHERE room_id = ?
        """
        try:
            cursor = self.connection.cursor()
            cursor.execute(query, (room_id,))
            user_ids = [row[0] for row in cursor.fetchall()]
            cursor.close()
            return {"status": "success", "user_ids": user_ids}
        except Exception as e:
            return {"status": "error", "message": str(e)}
