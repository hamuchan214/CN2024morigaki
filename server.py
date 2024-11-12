import socket
import threading
import sqlite3
import datetime

# Server configuration
HOST = '127.0.0.1'
PORT = 12345
clients = []
shutdown_flag = threading.Event()

# Initialize and setup the database
def setup_database():
    conn = sqlite3.connect('chat.db')
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS Users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS Rooms (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            room_name TEXT UNIQUE NOT NULL
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS Messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            room_id INTEGER,
            message TEXT,
            timestamp TEXT,
            FOREIGN KEY (user_id) REFERENCES Users (id),
            FOREIGN KEY (room_id) REFERENCES Rooms (id)
        )
    ''')
    conn.commit()
    conn.close()

# Store a message in the database
def store_message(username, room, message):
    conn = sqlite3.connect('chat.db')
    cursor = conn.cursor()
    
    # Get or create user
    cursor.execute("INSERT OR IGNORE INTO Users (username) VALUES (?)", (username,))
    cursor.execute("SELECT id FROM Users WHERE username = ?", (username,))
    user_id = cursor.fetchone()[0]
    
    # Get or create room
    cursor.execute("INSERT OR IGNORE INTO Rooms (room_name) VALUES (?)", (room,))
    cursor.execute("SELECT id FROM Rooms WHERE room_name = ?", (room,))
    room_id = cursor.fetchone()[0]
    
    # Insert message
    timestamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    cursor.execute("INSERT INTO Messages (user_id, room_id, message, timestamp) VALUES (?, ?, ?, ?)",
                   (user_id, room_id, message, timestamp))
    conn.commit()
    conn.close()

# Broadcast message to all clients in the room
def broadcast(message, client_socket):
    for client in clients:
        if client != client_socket:
            client.sendall(message.encode())

# Handle individual client connection
def handle_client(client_socket, client_address):
    print(f"New connection from {client_address}")
    clients.append(client_socket)

    try:
        while True:
            data = client_socket.recv(1024)  # Receive message from client
            if data:
                message = data.decode()
                print(f"Message from {client_address}: {message}")
                
                # Parse and store message in database
                # Expected format: "<username>:<room>:<message>"
                try:
                    username, room, msg_content = message.split(":", 2)
                    store_message(username, room, msg_content)
                except ValueError:
                    print("Invalid message format")
                
                broadcast(username + ": " + msg_content, client_socket)  # Send message to all clients
            else:
                break
    finally:
        client_socket.close()
        clients.remove(client_socket)
        print(f"Connection from {client_address} closed.")

# Monitor for shutdown command in a separate thread
def monitor_shutdown():
    global shutdown_flag
    while not shutdown_flag.is_set():
        command = input()
        if command.lower() == "shutdown":
            print("Shutting down the server...")
            shutdown_flag.set()

# Main server setup
def start_server():
    setup_database()  # Initialize the database
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind((HOST, PORT))
    server_socket.listen()
    print(f"Server started on {HOST}:{PORT}")

    # Start shutdown monitoring thread
    shutdown_thread = threading.Thread(target=monitor_shutdown)
    shutdown_thread.start()
    
    try:
        while not shutdown_flag.is_set():
            server_socket.settimeout(1.0)  # Check every second
            try:
                client_socket, client_address = server_socket.accept()
                thread = threading.Thread(target=handle_client, args=(client_socket, client_address))
                thread.start()
            except socket.timeout:
                continue  # Check if shutdown_flag is set
    finally:
        server_socket.close()
        print("Server has been closed.")

if __name__ == "__main__":
    start_server()
