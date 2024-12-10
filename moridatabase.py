import sqlite3
import asyncio
import hashlib
import uuid
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
        self.connection.row_factory = sqlite3.Row
        self.logger = setup_logger()

    async def execute_query(self, query, params=None):
        """非同期的にクエリを実行します"""
        loop = asyncio.get_running_loop()

        def execute():
            try:
                cursor = self.connection.cursor()
                cursor.execute(query, params or ())
                self.connection.commit()
                return {"status": "success", "data": cursor.fetchall()}
            except Exception as e:
                return {"status": "error", "message": str(e)}
            finally:
                cursor.close()

        return await loop.run_in_executor(None, execute)

    async def setup_database(self):
        """データベースのテーブルを初期化します"""
        queries = [
            """CREATE TABLE IF NOT EXISTS user (
                user_id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL UNIQUE,
                password TEXT NOT NULL,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            );""",
            """CREATE TABLE IF NOT EXISTS room (
                room_id INTEGER PRIMARY KEY AUTOINCREMENT,
                room_name TEXT NOT NULL UNIQUE,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            );""",
            """CREATE TABLE IF NOT EXISTS message (
                message_id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                room_id INTEGER NOT NULL,
                message TEXT NOT NULL,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(user_id) REFERENCES user(user_id),
                FOREIGN KEY(room_id) REFERENCES room(room_id)
            );""",
            """CREATE TABLE IF NOT EXISTS room_user (
                user_id INTEGER NOT NULL,
                room_id INTEGER NOT NULL,
                last_read_at DATETIME,
                PRIMARY KEY(user_id, room_id),
                FOREIGN KEY(user_id) REFERENCES user(user_id),
                FOREIGN KEY(room_id) REFERENCES room(room_id)
            );""",
        ]
        for query in queries:
            result = await self.execute_query(query)
            if result["status"] == "error":
                self.logger.error(f"Failed to execute query: {query}")
                return result
        self.logger.info("Database setup completed.")
        return {"status": "success"}

    async def add_user(self, username, password):
        """新規ユーザーを追加"""
        hashed_password = hashlib.sha256(password.encode()).hexdigest()
        query = "INSERT INTO user (username, password) VALUES (?, ?)"
        result = await self.execute_query(query, (username, hashed_password))
        if result["status"] == "success":
            self.logger.info(f"User added: {username}")
        else:
            self.logger.error(f"Failed to add user: {username} - {result['message']}")
        return result

    async def login(self, username, password):
        """ユーザーのログインを処理"""
        query = "SELECT user_id, password FROM user WHERE username = ?"
        result = await self.execute_query(query, (username,))
        if result["status"] == "error" or not result["data"]:
            return {"status": "error", "message": "Invalid username or password"}

        row = result["data"][0]
        hashed_password = hashlib.sha256(password.encode()).hexdigest()
        if row["password"] == hashed_password:
            session_id = str(uuid.uuid4())
            return {
                "status": "success",
                "user_id": row["user_id"],
                "session_id": session_id,
            }
        else:
            return {"status": "error", "message": "Invalid username or password"}

    async def create_room(self, room_name):
        """部屋を作成"""
        query = "INSERT INTO room (room_name) VALUES (?)"
        result = await self.execute_query(query, (room_name,))
        if result["status"] == "success":
            self.logger.info(f"Room created: {room_name}")
        else:
            self.logger.error(f"Failed to create room: {room_name}")
        return result

    async def save_message(self, user_id, room_id, message):
        """メッセージを保存"""
        query = "INSERT INTO message (user_id, room_id, message) VALUES (?, ?, ?)"
        return await self.execute_query(query, (user_id, room_id, message))

    async def get_messages_by_room(self, room_id):
        """部屋のメッセージを取得"""
        query = "SELECT message_id, user_id, message, timestamp FROM message WHERE room_id = ? ORDER BY timestamp ASC"
        return await self.execute_query(query, (room_id,))

    async def get_room_id_by_name(self, room_name):
        """部屋名から部屋IDを取得"""
        query = "SELECT room_id FROM room WHERE room_name = ?"
        result = await self.execute_query(query, (room_name,))
        if result["status"] == "success" and result["data"]:
            return {"status": "success", "room_id": result["data"][0]["room_id"]}
        else:
            return {"status": "error", "message": "Room not found"}
