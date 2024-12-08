import socket

server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server_socket.bind(("127.0.0.1", 6001))
server_socket.listen(3)

while True:
    client_socket, client_address = server_socket.accept()
    data = client_socket.recv(1024)
    print("Received data:", data.decode())
    client_socket.sendall(b"Hello from the server!")