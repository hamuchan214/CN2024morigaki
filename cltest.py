import socket
import json
import asyncio

class ChatClient:
    def __init__(self, host='127.0.0.1', port=6001):
        self.host = host
        self.port = port
        self.client_socket = None
        self.session_id = None

    async def connect(self):
        """Connect to the chat server."""
        self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.client_socket.connect((self.host, self.port))

    async def send_request(self, action, data):
        """Send a request to the chat server."""
        request = {
            "action": action,
            **data  # 'data' を直接リクエストに統合
        }

        # リクエストをJSON文字列にして送信
        self.client_socket.sendall(json.dumps(request).encode())

        # サーバーからのレスポンスを受信
        response_data = self.client_socket.recv(1024)
        response = json.loads(response_data.decode())
        return response

    async def add_user(self, username, password):
        """Add a new user."""
        response = await self.send_request("add_user", {"username": username, "password": password})
        return response

    async def login(self, username, password):
        """Login the user."""
        response = await self.send_request("login", {"username": username, "password": password})
        return response

    async def create_room(self, session_id, room_name):
        """Create a new room."""
        response = await self.send_request("create_room", {"session_id": session_id, "room_name": room_name})
        return response

    async def send_message(self, session_id, room_id, message):
        """Send a message to the room."""
        response = await self.send_request("add_message", {"session_id": session_id, "room_id": room_id, "message": message})
        return response

    async def get_messages(self, room_id):
        """Get messages from a room."""
        response = await self.send_request("get_messages_by_room", {"room_id": room_id})
        return response

    async def start(self):
        """Start the client and interact with the server."""
        # ユーザーの追加
        username = input("Enter username: ")
        password = input("Enter password: ")
        
        print("Adding user...")
        add_user_response = await self.add_user(username, password)
        print(f"Received response: {add_user_response}")

        if add_user_response["status"] != "success":
            print("Failed to add user. Exiting...")
            return

        # ログイン
        print("Logging in user...")
        login_response = await self.login(username, password)
        print(f"Received response: {login_response}")

        if login_response["status"] == "success":
            self.session_id = login_response["session_id"]
            print(f"Session ID: {self.session_id}")
        else:
            print("Login failed. Exiting...")
            return

        # チャットルームの作成
        room_name = input("Enter room name: ")
        print("Creating chat room...")
        create_room_response = await self.create_room(self.session_id, room_name)
        print(f"Received response: {create_room_response}")

        if create_room_response["status"] == "success":
            room_id = create_room_response["room_id"]
            print(f"Room ID: {room_id}")
        else:
            print("Failed to create room. Exiting...")
            return

        # メッセージの送信と表示
        while True:
            message_content = input("Enter message (or type 'exit' to quit): ")
            if message_content.lower() == "exit":
                break

            print("Sending message...")
            add_message_response = await self.send_message(self.session_id, room_id, message_content)
            print(f"Received response: {add_message_response}")

            if add_message_response["status"] != "success":
                print("Failed to send message. Exiting...")
                break

            # 送信したメッセージを含む全メッセージを取得して表示
            print("Retrieving messages from room...")
            get_messages_response = await self.get_messages(room_id)
            print(f"Received response: {get_messages_response}")

            if get_messages_response["status"] == "success":
                messages = get_messages_response.get("messages", [])
                print(f"Messages in room {room_id}:")
                for msg in messages:
                    print(f"- {msg}")
            else:
                print("Failed to retrieve messages.")

        print("Exiting chat...")

if __name__ == "__main__":
    client = ChatClient()
    asyncio.run(client.connect())  # サーバーに接続
    asyncio.run(client.start())  # チャット開始