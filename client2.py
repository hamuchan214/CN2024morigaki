import socket
import json

def send_request(action, data):
    """Send a request to the chat server."""
    host = '127.0.0.1'
    port = 6001

    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as client_socket:
            client_socket.connect((host, port))
            request = {"action": action, **data}
            client_socket.sendall(json.dumps(request).encode())  # リクエストを送信

            response_data = client_socket.recv(1024)  # サーバーからのレスポンスを受信
            response = json.loads(response_data.decode())
            return response
    except Exception as e:
        return {"status": "error", "message": str(e)}

# 検証用のコード
if __name__ == "__main__":
    username = "test_user"
    password = "test_password"

    # 1. ユーザーの追加
    print("Adding user...")
    add_user_response = send_request("add_user", {"username": username, "password": password})
    print(f"Response: {add_user_response}")

    # 2. ユーザーのログイン
    print("Logging in user...")
    login_response = send_request("login", {"username": username, "password": password})
    print(f"Response: {login_response}")

    if login_response["status"] == "success":
        session_id = login_response["session_id"]
        print(f"Session ID: {session_id}")
    else:
        print("Login failed.")
