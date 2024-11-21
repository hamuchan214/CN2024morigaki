import socket
import json

client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
client_socket.connect(('127.0.0.1', 6001))

test_request = {
    "action": "add_user",
    "username": "ham",
    "password": "1234"
}

client_socket.sendall(json.dumps(test_request).encode())

response = client_socket.recv(1024)
print("Response:", json.loads(response.decode()))

client_socket.close()
