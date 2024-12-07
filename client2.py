import socket
import json

def send_request(action, data):
    """Send a request to the chat server."""
    host = '127.0.0.1'
    port = 6001

    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as client_socket:
            client_socket.connect((host, port))
            
            # リクエストデータの形式を修正
            request = {
                "action": action,
                **data  # 'data' を直接リクエストに統合
            }
            client_socket.sendall(json.dumps(request).encode())  # リクエストを送信

            response_data = client_socket.recv(1024)  # サーバーからのレスポンスを受信
            response = json.loads(response_data.decode())
            return response
    except Exception as e:
        return {"status": "error", "message": str(e)}


# Verification Code
if __name__ == "__main__":
    username = "test_user"
    password = "test_password"

    # 1. Add User
    print("Adding user...")
    add_user_response = send_request("add_user", {"username": username, "password": password})
    print(f"Response: {add_user_response}")

    if add_user_response["status"] != "success":
        print("Failed to add user. Exiting...")
        exit()

    # 2. Login User
    print("Logging in user...")
    login_response = send_request("login", {"username": username, "password": password})
    print(f"Response: {login_response}")

    if login_response["status"] == "success":
        session_id = login_response["session_id"]
        print(f"Session ID: {session_id}")
    else:
        print("Login failed. Exiting...")
        exit()

    # 3. Create Room
    print("Creating chat room...")
    room_name = "Test Room"
    create_room_response = send_request("create_room", {"session_id": session_id, "room_name": room_name})
    print(f"Response: {create_room_response}")

    if create_room_response["status"] == "success":
        room_id = create_room_response["room_id"]
        print(f"Room ID: {room_id}")
    else:
        print("Failed to create room. Exiting...")
        exit()

    # 4. Send Message
    print("Sending message to room...")
    message_content = "Hello, this is a test message."
    add_message_response = send_request(
        "add_message",
        {"session_id": session_id, "room_id": room_id, "message": message_content}
    )
    print(f"Response: {add_message_response}")

    if add_message_response["status"] != "success":
        print("Failed to send message. Exiting...")
        exit()

    # 5. Retrieve Messages
    print("Retrieving messages from room...")
    get_messages_response = send_request("get_messages_by_room", {"room_id": room_id})
    print(f"Response: {get_messages_response}")

    if get_messages_response["status"] == "success":
        messages = get_messages_response.get("messages", [])
        print(f"Messages in room {room_id}:")
        for msg in messages:
            print(f"- {msg}")
    else:
        print("Failed to retrieve messages. Exiting...")
        exit()

    print("All tests completed successfully!")
