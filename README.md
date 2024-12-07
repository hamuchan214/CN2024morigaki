# コンピューターネットワーク課題

# チャットサーバープログラムの概要

このプログラムは、非同期的なチャットサーバーを実現するためのPythonスクリプトです。`asyncio`ライブラリを用いて非同期通信を行い、複数のクライアントとの通信を処理します。また、SQLiteデータベースを利用してユーザー管理やメッセージ管理を行います。

## 主な機能

- ユーザー登録 (`add_user`)
- ログイン機能 (`login`)
- チャットルームの作成 (`create_room`)
- メッセージの送信・受信 (`add_message`, `get_messages_by_room`)
- ルームメンバーの管理 (`get_room_members`, `add_user_to_room`)
- セッション管理

## クラスとメソッドの詳細

### `ChatServer` クラス

`ChatServer` クラスは、サーバー全体の管理を行います。以下に主なメソッドを説明します。

#### コンストラクタ (`__init__`)
```
def __init__(self, host='127.0.0.1', port=6001):
    self.host = host
    self.port = port
    self.db = AsyncDatabase('chat.db')
    self.sessions = {}
    self.room_users = {}
    self.socket_user_map = {}
    self.logger = setup_logger()
```
- サーバーのホスト（デフォルトは`127.0.0.1`）とポート（デフォルトは`6001`）を設定します。
- データベースインスタンスを作成します。
- セッション、ルーム、ソケットとユーザーの関連を管理するための辞書を初期化します。
- ログ用のロガーを設定します。

#### セッション管理

##### `create_session`
```
def create_session(self, user_id: str) -> str:
    session_id = generate_session_id(user_id)
    expiration_time = time.time() + 3600
    self.sessions[session_id] = (user_id, expiration_time)
    self.logger.info(f"Session created for user {user_id}: {session_id}")
    return session_id
```
- ユーザーIDからセッションIDを生成し、セッションを作成します。

**リクエスト例**:
{
  "user_id": "john_doe"
}

**返り値例**:
{
  "session_id": "abc123",
  "status": "success"
}

##### `validate_session`
```
def validate_session(self, session_id: str) -> str | None:
    session = self.sessions.get(session_id)
    if session and time.time() < session[1]:
        self.logger.debug(f"Session {session_id} is valid for user {session[0]}")
        return session[0]
    self.sessions.pop(session_id, None)
    self.logger.warning(f"Session {session_id} is invalid or expired")
    return None
```
- セッションIDが有効かを検証し、有効な場合はユーザーIDを返します。

**リクエスト例**:
{
  "session_id": "abc123"
}

**返り値例**:
{
  "user_id": "john_doe",
  "status": "success"
}

#### ユーザー管理

##### `initialize_user_rooms`
```
async def initialize_user_rooms(self, user_id: str, client_socket: socket.socket):
    rooms = await self.db.get_rooms_by_user_async(user_id)
    for room_id in rooms:
        self.room_users.setdefault(room_id, []).append(client_socket)
    self.logger.info(f"Initialized rooms for user {user_id}: {rooms}")
    
    self.socket_user_map[client_socket] = user_id
    self.logger.info(f"Socket {client_socket.getpeername()} mapped to user {user_id}")
```
- ユーザーが所属する部屋を取得し、そのユーザーを各部屋にマップします。
- ソケットとユーザーIDを紐づける。

**リクエスト例**:
{
  "user_id": "john_doe",
  "client_socket": "socket1"
}

**返り値例**:
{
  "status": "success",
  "message": "Rooms initialized for user john_doe"
}

##### `handle_user_disconnect`
```
async def handle_user_disconnect(self, client_socket: socket.socket):
    user_id = self.socket_user_map.get(client_socket)
    if user_id:
        self.logger.info(f"User {user_id} disconnected.")
        for room_id, sockets in list(self.room_users.items()):
            if client_socket in sockets:
                sockets.remove(client_socket)
                if not sockets:
                    del self.room_users[room_id]
        del self.socket_user_map[client_socket]
        self.logger.info(f"Socket {client_socket.getpeername()} unmapped from user {user_id}")
```
- ユーザーが切断された際に、そのユーザーをすべてのルームから削除し、ソケットとユーザーIDのマッピングを解除します。

**リクエスト例**:
{
  "client_socket": "socket1"
}

**返り値例**:
{
  "status": "success",
  "message": "User john_doe disconnected and cleaned up"
}

#### メッセージ送信

##### `broadcast_message_to_room`
```
async def broadcast_message_to_room(self, room_id: str, message: str, sender_socket: socket.socket):
    for user_socket in self.room_users.get(room_id, []):
        if user_socket != sender_socket:
            await self._send_message(user_socket, message)
    self.logger.info(f"Broadcast message to room {room_id}: {message[:20]}...")
```
- 指定された部屋の全メンバーにメッセージを送信します。

**リクエスト例**:
{
  "room_id": "room1",
  "message": "Hello everyone!",
  "sender_socket": "socket1"
}

**返り値例**:
{
  "status": "success",
  "message": "Message broadcasted to room room1"
}

##### `_send_message`
```
async def _send_message(self, client_socket: socket.socket, message: str):
    try:
        if isinstance(message, dict):
            message = json.dumps(message)
        if isinstance(message, str):
            message = message.encode("utf-8")
        await asyncio.get_running_loop().sock_sendall(client_socket, message)
        self.logger.debug(f"Message sent: {message.decode('utf-8')}")
    except Exception as e:
        self.logger.error(f"Failed to send message to {client_socket.getpeername()}: {e}")
```
- メッセージをクライアントに送信します。エラーハンドリングも行います。

**リクエスト例**:
{
  "client_socket": "socket1",
  "message": "Hello!"
}

**返り値例**:
{
  "status": "success",
  "message": "Message sent successfully"
}

#### クライアントリクエストの処理

##### `handle_client`
```
async def handle_client(self, client_socket):
    try:
        while True:
            data = await asyncio.get_running_loop().run_in_executor(None, client_socket.recv, 1024)
            if not data:
                break
            request = json.loads(data.decode())
            session_id = request.get('session_id')
            if not session_id:
                action = request.get('action')
                if action and action in ['add_user', 'login']:
                    response = await self.route_request(action, request, client_socket)
                    await self._send_message(client_socket, response)
                    continue
                else:
                    await self._send_message(client_socket, {"status": "error", "message": "Missing session_id"})
                    continue
            action = request.get('action')
            if action:
                response = await self.route_request(action, request, client_socket)
                await self._send_message(client_socket, response)
    except Exception as e:
        self.logger.error(f"Error handling client {client_socket.getpeername()}: {e}")
        await self._send_message(client_socket, {"status": "error", "message": str(e)})
    finally:
        self.logger.debug(f"Client {client_socket.getpeername()} handling complete.")
```
- クライアントからのリクエストを処理し、対応するアクションを実行します。

**リクエスト例**:
{
  "session_id": "abc123",
  "action": "add_user",
  "username": "john_doe",
  "password": "password123"
}

**返り値例**:
{
  "status": "success",
  "message": "User john_doe added successfully"
}

#### リクエストのルーティング

##### `route_request`
```
async def route_request(self, action: str, request: dict, client_socket: socket.socket):
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
        response = await handler(request)
        return response
    except Exception as e:
        self.logger.error(f"Error in handler for action '{action}': {e}")
        return {"status": "error", "message": str(e)}
```
- リクエストに基づいて適切なハンドラーを呼び出します。

**リクエスト例**:
{
  "action": "add_user",
  "username": "john_doe",
  "password": "password123"
}

**返り値例**:
{
  "status": "success",
  "message": "User john_doe added successfully"
}

## デコレーター

### `extract_request_params`
```
def extract_request_params(required_params: list[str]) -> Callable:
    def decorator(func: Callable):
        async def wrapper(self, request: dict, *args, **kwargs):
            missing_params = [p for p in required_params if p not in request or not request[p]]
            if missing_params:
                return {"status": "error", "message": f"Missing parameters: {missing_params}"}
            filtered_kwargs = {param: request[param] for param in required_params}
            return await func(self, *args, **filtered_kwargs)
        return wrapper
    return decorator
```
- リクエストから必要なパラメータを抽出し、検証するデコレーターです。

**リクエスト例**:
{
  "username": "john_doe"
}

**返り値例**:
{
  "status": "error",
  "message": "Missing parameters: ['password']"
}

### `require_valid_session`
```
def require_valid_session(func: Callable) -> Callable:
    async def wrapper(self, session_id: str, **kwargs):
        user_id = self.validate_session(session_id)
        if not user_id:
            return {"status": "error", "message": "Invalid or expired session"}
        return await func(self, user_id=user_id, **kwargs)
    return wrapper
```
- セッションIDを検証し、有効な場合にのみ処理を実行するデコレーターです。

**リクエスト例**:
{
  "session_id": "abc123"
}

**返り値例**:
{
  "user_id": "john_doe",
  "status": "success"
}

このドキュメントをMarkdown形式でコピーして使用できます。