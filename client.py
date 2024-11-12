import socket
import threading
import curses  # cursesライブラリを使用

# Server configuration
HOST = '127.0.0.1'  # サーバーのIPアドレス
PORT = 12345        # サーバーのポート番号

# サーバーからのメッセージを受信して表示する
def receive_messages(client_socket, stdscr):
    stdscr.scrollok(True)  # 画面のスクロールを許可

    while True:
        try:
            message = client_socket.recv(1024).decode('utf-8')
            if message:
                stdscr.addstr("\n" + message)  # 新しいメッセージを追加
                stdscr.refresh()
            else:
                stdscr.addstr("\nServer has closed the connection.\n")
                client_socket.close()
                break
        except Exception as e:
            stdscr.addstr(f"\nAn error occurred: {e}\n")
            client_socket.close()
            break

# サーバーに接続し、チャットを開始する
def start_client(stdscr):
    stdscr.clear()  # 画面をクリア

    # ユーザー名の入力プロンプト表示
    stdscr.addstr(0, 0, "Enter your username: ")
    stdscr.refresh()
    curses.echo()  # 入力内容を表示
    username = stdscr.getstr(0, 19, 20).decode()  # ユーザー名を取得
    curses.noecho()  # 入力表示を終了

    # ルーム名の入力プロンプト表示
    stdscr.addstr(1, 0, "Enter room name: ")
    stdscr.refresh()
    curses.echo()  # 入力内容を表示
    room = stdscr.getstr(1, 15, 20).decode()  # ルーム名を取得
    curses.noecho()  # 入力表示を終了

    # サーバーに接続
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client_socket.connect((HOST, PORT))
    stdscr.addstr(2, 0, "Connected to the server.")
    stdscr.refresh()

    # メッセージ受信用のスレッドを開始
    threading.Thread(target=receive_messages, args=(client_socket, stdscr), daemon=True).start()

    # メッセージ送信ループ
    try:
        while True:
            stdscr.addstr(3, 0, "You: ")  # 常に同じ位置にプロンプトを表示
            stdscr.refresh()
            curses.echo()  # 入力内容を表示
            msg_content = stdscr.getstr(3, 5, 100).decode()  # ユーザー入力を取得
            curses.noecho()  # 入力表示を終了

            if msg_content.lower() == "exit":
                stdscr.addstr("\nExiting the chat.\n")
                break

            # サーバーに送信
            message = f"{username}:{room}:{msg_content}"
            client_socket.sendall(message.encode('utf-8'))
            stdscr.move(3, 5)  # 入力欄のカーソル位置をリセット
            stdscr.clrtoeol()  # 入力したメッセージを消去
            stdscr.refresh()

    except KeyboardInterrupt:
        stdscr.addstr("\nDisconnected from server.\n")
    finally:
        client_socket.close()

if __name__ == "__main__":
    curses.wrapper(start_client)
