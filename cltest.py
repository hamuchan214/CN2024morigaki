import socket
import json
import threading


class ChatClient:
    def __init__(self, host='127.0.0.1', port=6001):
        self.host = host
        self.port = port
        self.session_id = None
        self.room_id = None

    def send_request(self, action, data):
        """Send a request to the chat server."""
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as client_socket:
                client_socket.connect((self.host, self.port))

                # Format request data
                request = {
                    "action": action,
                    **data
                }
                client_socket.sendall(json.dumps(request).encode())  # Send request

                # Receive and decode response
                response_data = client_socket.recv(1024)
                response = json.loads(response_data.decode())
                return response
        except Exception as e:
            return {"status": "error", "message": str(e)}

    def add_user(self, username, password):
        """Register a new user."""
        return self.send_request("add_user", {"username": username, "password": password})

    def login(self, username, password):
        """Login an existing user."""
        response = self.send_request("login", {"username": username, "password": password})
        if response["status"] == "success":
            self.session_id = response["session_id"]
        return response

    def create_room(self, room_name):
        """Create a new chat room."""
        if not self.session_id:
            return {"status": "error", "message": "No active session. Please login first."}
        response = self.send_request("create_room", {"session_id": self.session_id, "room_name": room_name})
        if response["status"] == "success":
            self.room_id = response["room_id"]
        return response

    def send_message(self, message):
        """Send a message to the current room."""
        if not self.session_id or not self.room_id:
            return {"status": "error", "message": "Session or room ID missing. Please login and select a room first."}
        return self.send_request("add_message", {"session_id": self.session_id, "room_id": self.room_id, "message": message})


def listen_for_messages(host, port, room_id):
    """Continuously listen for incoming messages."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as client_socket:
        client_socket.connect((host, port))
        client_socket.sendall(json.dumps({"action": "join_room", "room_id": room_id}).encode())
        while True:
            data = client_socket.recv(1024)
            if not data:
                break
            print(json.loads(data.decode()))


if __name__ == "__main__":
    username = input("Enter username: ")
    password = input("Enter password: ")

    client = ChatClient()
    client.add_user(username, password)
    client.login(username, password)

    room_name = input("Enter room name: ")
    client.create_room(room_name)

    # Start listening thread
    threading.Thread(target=listen_for_messages, args=(client.host, client.port, client.room_id), daemon=True).start()

    while True:
        message = input("Enter message: ")
        client.send_message(message)