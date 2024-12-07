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
                # Only include session_id if it's set (login or room operations)
                if self.session_id:
                    request["session_id"] = self.session_id

                client_socket.sendall(json.dumps(request).encode())  # Send request

                # Receive and decode response
                response_data = client_socket.recv(1024)
                response = json.loads(response_data.decode())
                print("Server Response:", response)  # Print the server's response
                return response
        except Exception as e:
            return {"status": "error", "message": str(e)}

    def add_user(self, username, password):
        """Register a new user."""
        response = self.send_request("add_user", {"username": username, "password": password})
        if response["status"] == "success":
            print(f"User '{username}' registered successfully.")
        else:
            print(f"Failed to register user '{username}': {response.get('message')}")
        return response

    def login(self, username, password):
        """Login an existing user."""
        response = self.send_request("login", {"username": username, "password": password})
        if response["status"] == "success":
            self.session_id = response["session_id"]
            print(f"User '{username}' logged in successfully.")
        else:
            print(f"Failed to login for user '{username}': {response.get('message')}")
        return response

    def create_room(self, room_name):
        """Create a new chat room."""
        if not self.session_id:
            print("No active session. Please login first.")
            return {"status": "error", "message": "No active session. Please login first."}
        response = self.send_request("create_room", {"room_name": room_name})
        if response["status"] == "success":
            self.room_id = response["room_id"]
            print(f"Room '{room_name}' created successfully.")
        else:
            print(f"Failed to create room '{room_name}': {response.get('message')}")
        return response

    def send_message(self, message):
        """Send a message to the current room."""
        if not self.session_id or not self.room_id:
            print("Session or room ID missing. Please login and select a room first.")
            return {"status": "error", "message": "Session or room ID missing. Please login and select a room first."}
        response = self.send_request("add_message", {"room_id": self.room_id, "message": message})
        if response["status"] == "success":
            print(f"Message sent to room {self.room_id}: {message}")
        else:
            print(f"Failed to send message to room {self.room_id}: {response.get('message')}")
        return response

    def join_or_create_room(self, room_name):
        """Join a room or create it if it doesn't exist."""
        if not self.session_id:
            print("No active session. Please login first.")
            return {"status": "error", "message": "No active session. Please login first."}

        # Check if the room exists by attempting to join it
        response = self.send_request("get_rooms_by_user", {"user_id": self.session_id})
        rooms = response.get("rooms", [])
        room_found = False
        for room in rooms:
            if room["name"] == room_name:
                self.room_id = room["room_id"]
                room_found = True
                break

        if room_found:
            print(f"Joined existing room '{room_name}'.")
        else:
            # Room doesn't exist, create a new one
            print(f"Room '{room_name}' does not exist. Creating a new room.")
            response = self.create_room(room_name)
            if response["status"] == "success":
                print(f"Successfully created and joined room '{room_name}'.")
        return response


def listen_for_messages(host, port, room_id):
    """Continuously listen for incoming messages."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as client_socket:
        client_socket.connect((host, port))
        client_socket.sendall(json.dumps({"session_id": None, "action": "join_room", "room_id": room_id}).encode())
        while True:
            data = client_socket.recv(1024)
            if not data:
                break
            response = json.loads(data.decode())
            print("Incoming Message:", response)  # Print the incoming messages
            # Optionally, you can add message handling here


if __name__ == "__main__":
    username = input("Enter username: ")
    password = input("Enter password: ")

    client = ChatClient()

    # Register user
    client.add_user(username, password)

    # Login user
    client.login(username, password)

    # Join or create room
    room_name = input("Enter room name: ")
    client.join_or_create_room(room_name)

    # Start listening thread
    threading.Thread(target=listen_for_messages, args=(client.host, client.port, client.room_id), daemon=True).start()

    while True:
        message = input("Enter message: ")
        client.send_message(message)