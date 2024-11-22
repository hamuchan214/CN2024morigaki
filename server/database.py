import sqlite3
import asyncio
import hashlib


class AsyncDatabase:
    def __init__(self, db_name):
        self.db_name = db_name
        self.connection = sqlite3.connect(db_name, check_same_thread=False)
        self.connection.row_factory = sqlite3.Row  # Allows accessing columns by name
        self.server = None

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
        query = "SELECT user_id, password FROM User WHERE username = ?"
        
        def authenticate():
            try:
                cursor = self.connection.cursor()
                cursor.execute(query, (username,))
                row = cursor.fetchone()
                cursor.close()
                
                print(f"Database returned row: {row}")  # デバッグ出力

                if not row:
                    return {"status": "error", "message": "Invalid username or password"} 
                
                user_id, stored_password = row
                print(f"user_id: {user_id}, stored_password: {stored_password}")  # デバッグ出力

                hashed_password = hashlib.sha256(password.encode()).hexdigest()
                print(f"hashed_password: {hashed_password}")  # デバッグ出力

                if hashed_password == stored_password:
                    session_id = self.server.create_session(user_id)
                    print(f"Session created: {session_id}")  # デバッグ出力
                    return {"status": "success", "user_id": user_id,"session_id": session_id}
                else:
                    return {"status": "error", "message": "Invalid username or password"}
            except Exception as e:
                return {"status": "error", "message": str(e)}


        return await asyncio.get_running_loop().run_in_executor(None, authenticate)


    async def add_user(self, username, password):
        # ハッシュ化されたパスワードを生成
        hashed_password = hashlib.sha256(password.encode()).hexdigest()
        query = f"INSERT INTO User (username, password) VALUES ('{username}', '{hashed_password}');"
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


    async def update_user_async(self, user_id, new_password, callback):
        hashed_password = hashlib.sha256(new_password.encode()).hexdigest()
        query = f"UPDATE User SET password = '{hashed_password}' WHERE user_id = {user_id};"
        try:
            cursor = self.connection.cursor()
            cursor.execute(query)
            self.connection.commit()
            cursor.close()
            return {"status": "success"}
        except Exception as e:
            return {"status": "error", "message": str(e)}

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