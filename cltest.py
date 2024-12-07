import asyncio
import json
import socket

class ChatClient:
    def __init__(self, host='127.0.0.1', port=6001):
        self.host = host
        self.port = port
        self.client_socket = None

    async def connect(self):
        """Connect to the chat server."""
        self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.client_socket.connect((self.host, self.port))
        print(f"Connected to {self.host}:{self.port}")

    async def send_request(self, request):
        """Send a request to the server."""
        message = json.dumps(request)
        self.client_socket.sendall(message.encode())

    async def receive_response(self):
        """Receive and display the response from the server."""
        data = await asyncio.get_running_loop().run_in_executor(None, self.client_socket.recv, 1024)
        
        # Check if data is empty
        if not data:
            print("Received empty data from the server")
            return None

        try:
            response = json.loads(data.decode())
        except json.JSONDecodeError:
            print(f"Failed to decode response: {data}")
            return None

        # Display the entire response JSON for debugging purposes
        print(f"Received response: {json.dumps(response, indent=4)}")
        
        return response

    async def add_user(self, username, password):
        """Add a new user."""
        request = {
            "action": "add_user",
            "username": username,
            "password": password
        }
        await self.send_request(request)
        response = await self.receive_response()
        if response and response.get("status") == "success":
            print(f"User {username} added successfully")
        else:
            print(f"Failed to add user: {response.get('message') if response else 'No response'}")

    async def login(self, username, password):
        """Log in to the server."""
        request = {
            "action": "login",
            "username": username,
            "password": password
        }
        await self.send_request(request)
        response = await self.receive_response()
        if response and response.get("status") == "success":
            print(f"Login successful, session_id: {response['session_id']}")
        else:
            print(f"Login failed: {response.get('message') if response else 'No response'}")

    async def start(self):
        """Start the client interaction."""
        await self.connect()

        # Example of adding a user and then logging in
        username = input("Enter username: ")
        password = input("Enter password: ")

        await self.add_user(username, password)
        await self.login(username, password)

# Start the client
client = ChatClient()
asyncio.run(client.start())