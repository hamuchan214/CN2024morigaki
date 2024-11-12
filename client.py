import socket
import threading

# Server configuration
HOST = '127.0.0.1'  # サーバーのIPアドレス
PORT = 12345        # サーバーのポート番号

# サーバーからのメッセージを受信し、画面に表示する関数
def receive_messages(client_socket):
    while True:
        try:
            message = client_socket.recv(1024).decode('utf-8')
            if message:
                print("\n" + message)  # 新しい行でメッセージを表示
            else:
                print("Server has closed the connection.")
                client_socket.close()
                break
        except Exception as e:
            print("An error occurred:", e)
            client_socket.close()
            break

# サーバーに接続し、メッセージ送信を開始する
def start_client():
    # ユーザー名とルーム名を設定
    username = input("Enter your username: ")
    room = input("Enter room name: ")

    # サーバーに接続
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client_socket.connect((HOST, PORT))
    print("Connected to the server.")

    # メッセージ受信用のスレッドを開始
    threading.Thread(target=receive_messages, args=(client_socket,), daemon=True).start()

    # サーバーにメッセージを送信
    try:
        while True:
            msg_content = input("You: ")
            if msg_content.lower() == "exit":
                print("Exiting the chat.")
                break
            message = f"{username}:{room}:{msg_content}"
            client_socket.sendall(message.encode('utf-8'))
    except KeyboardInterrupt:
        print("\nDisconnected from server.")
    finally:
        client_socket.close()

if __name__ == "__main__":
    start_client()
