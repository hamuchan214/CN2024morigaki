import sqlite3
import asyncio
import hashlib


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
