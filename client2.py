import socket
import json
import threading
import sys

class ChatClient:
    def __init__(self, host='127.0.0.1', port=6001):
        """Initialize the chat client."""
        self.host = host
        self.port = port
        self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.client_socket.connect((self.host, self.port))
        self.listening = True  # To control the message listener thread

    def send_request(self, action, data):
        """Send a request to the chat server."""
        try:
            request = {"action": action, **data}
            self.client_socket.sendall(json.dumps(request).encode())  # Send request to the server

            response_data = self.client_socket.recv(1024)  # Receive response
            response = json.loads(response_data.decode())

            return response
        except json.JSONDecodeError:
            return {"status": "error", "message": "Invalid response from server"}
        except Exception as e:
            return {"status": "error", "message": str(e)}

    def display_new_message(self, response):
        """Display a new message received from the server."""
        print(f"New message received in room {response['room_id']}: {response['message']}: {response['user_name']}")

    def listen_for_messages(self):
        """Continuously listen for new messages from the server."""
        while self.listening:
            try:
                response_data = self.client_socket.recv(1024)
                if response_data:
                    response = json.loads(response_data.decode())
                    if response.get("action") == "new_message":
                        self.display_new_message(response)
            except json.JSONDecodeError:
                print("Received invalid message format from server.")
            except Exception as e:
                print(f"Error receiving message: {str(e)}")
                self.listening = False  # Stop listening if an error occurs
                break

    def close(self):
        """Close the connection to the server."""
        self.listening = False  # Stop the listener thread
        self.client_socket.close()
        print("Connection closed.")

    def join_room(self, session_id, room_name):
        """Join a chat room by its name."""
        response = self.send_request("join_room", {"session_id": session_id, "room_name": room_name})
        if response["status"] == "success":
            print(f"Successfully joined room: {room_name}")
            return True
        else:
            print(f"Failed to join room: {response['message']}")
            return False


# Verification Code
if __name__ == "__main__":
    username = "test_user"
    password = "test_password"

    try:
        # Create a chat client instance
        client = ChatClient()

        # 1. Add User
        print("Adding user...")
        add_user_response = client.send_request("add_user", {"username": username, "password": password})
        print(f"Response: {add_user_response}")

        if add_user_response["status"] != "success":
            print("Failed to add user. Exiting...")
            client.close()
            sys.exit()

        # 2. Login User
        print("Logging in user...")
        login_response = client.send_request("login", {"username": username, "password": password})
        print(f"Response: {login_response}")

        if login_response["status"] == "success":
            session_id = login_response["session_id"]
            print(f"Session ID: {session_id}")
        else:
            print("Login failed. Exiting...")
            client.close()
            sys.exit()

        # 3. Create Room
        print("Creating chat room...")
        room_name = "Test Room"
        create_room_response = client.send_request("create_room", {"session_id": session_id, "room_name": room_name})
        print(f"Response: {create_room_response}")

        if create_room_response["status"] == "success":
            room_id = create_room_response["room_id"]
            print(f"Room ID: {room_id}")
        else:
            print("Failed to create room. Exiting...")
            client.close()
            sys.exit()

        #4. Join Room
        join_room_response = client.join_room(session_id,room_name)
        if not join_room_response:
            print("Failed to join room. Exiting...")
            client.close()
            sys.exit()

        # 5. Send Message
        print("Sending message to room...")
        message_content = "Hello, this is a test message."
        add_message_response = client.send_request(
            "add_message",
            {"session_id": session_id, "room_id": room_id, "message": message_content}
        )
        print(f"Response: {add_message_response}")

        if add_message_response["status"] != "success":
            print("Failed to send message. Exiting...")
            client.close()
            sys.exit()
            

        # Start listening for new messages after sending the message
        print("Waiting for new messages...")
        message_listener_thread = threading.Thread(target=client.listen_for_messages)
        message_listener_thread.daemon = True  # Allow the thread to exit when the main program exits
        message_listener_thread.start()

        # Allow the user to type commands or exit the application
        while True:
            user_input = input("Enter 'exit' to quit or 'send' to send another message: ").strip().lower()
            if user_input == "exit":
                print("Exiting...")
                client.close()
                break
            elif user_input == "send":
                new_message = input("Enter your message: ")
                response = client.send_request(
                    "add_message",
                    {"session_id": session_id, "room_id": room_id, "message": new_message}
                )
                print(f"Response: {response}")

    except KeyboardInterrupt:
        print("\nInterrupted by user. Exiting...")
        client.close()
        sys.exit()
    except Exception as e:
        print(f"Unexpected error: {str(e)}")
        sys.exit()
