import sqlite3
import asyncio
import json
import socket
from functools import partial

class AsyncDatabase:
    def __init__(self, db_name):
        self.db_name = db_name
        self.db = sqlite3.connect(db_name, check_same_thread=False)
        self.db.row_factory = sqlite3.Row  # Allows accessing columns by name

    def execute_async(self, query, callback):
        loop = asyncio.get_event_loop()
        loop.run_in_executor(None, self._execute, query, callback)

    def _execute(self, query, callback):
        try:
            cursor = self.db.cursor()
            cursor.execute(query)
            self.db.commit()
            cursor.close()
            callback(None)
        except Exception as e:
            callback(e)

    def query_async(self, query, callback):
        loop = asyncio.get_event_loop()
        loop.run_in_executor(None, self._query, query, callback)

    def _query(self, query, callback):
        try:
            cursor = self.db.cursor()
            cursor.execute(query)
            rows = cursor.fetchall()
            cursor.close()
            callback(rows, None)
        except Exception as e:
            callback([], e)

    def setup_database(self, callback):
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
            self.execute_async(query, partial(self._setup_callback, callback))

    def _setup_callback(self, callback, error):
        if error:
            callback(error)
        else:
            callback(None)

    def add_user_async(self, username, password, callback):
        query = f"INSERT INTO User (username, password) VALUES ('{username}', '{password}');"
        self.execute_async(query, callback)

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
    def __init__(self, host='127.0.0.1', port=5000):
        self.host = host
        self.port = port
        self.db = AsyncDatabase('chat.db')
    
    def start_server(self):
        """サーバーを起動して接続を待機"""
        server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_socket.bind((self.host, self.port))
        server_socket.listen(5)
        print(f'Server listening on {self.host}:{self.port}')
        
        while True:
            client_socket, client_address = server_socket.accept()
            print(f"Connection from {client_address}")
            # クライアントとの通信を非同期で処理
            asyncio.run(self.handle_client(client_socket))

    async def handle_client(self, client_socket):
        """クライアントからのJSONデータを受け取り、処理する"""
        try:
            data = client_socket.recv(1024)  # データを受け取る
            if data:
                # 受け取ったデータをJSON形式として処理
                request = json.loads(data.decode())
                action = request.get('action')
                response = {}

                if action == 'add_user':
                    username = request.get('username')
                    password = request.get('password')
                    # データベースへの追加処理
                    await self.db.add_user_async(username, password, self._send_response(client_socket, response))
                elif action == 'get_user':
                    user_id = request.get('user_id')
                    # ユーザー情報取得処理
                    await self.db.get_user_async(user_id, self._send_response(client_socket, response))
                # 他の処理も同様に追加
                else:
                    response = {'error': 'Invalid action'}
                
                # もしデータが無ければエラー応答を返す
                if not response:
                    response = {'error': 'No data received'}
                client_socket.send(json.dumps(response).encode())  # 結果を送信

        except Exception as e:
            response = {'error': str(e)}
            client_socket.send(json.dumps(response).encode())  # エラー応答を送信
        finally:
            client_socket.close()

    def _send_response(self, client_socket, response):
        """レスポンスを非同期に送信する"""
        def callback(data, error):
            if error:
                response['error'] = str(error)
            else:
                response['data'] = data
            client_socket.send(json.dumps(response).encode())
        return callback

if __name__ == '__main__':
    server = ChatServer()
    server.start_server()