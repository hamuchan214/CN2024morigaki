import socket
import threading
import curses  # cursesライブラリを使用
import json  # JSONの操作を追加


# Server configuration
HOST = "127.0.0.1"  # サーバーのIPアドレス
PORT = 6001  # サーバーのポート番号


def receive_messages(client_socket, stdscr, messages):
    stdscr.scrollok(True)  # 画面のスクロールを許可

    while True:
        try:
            message = client_socket.recv(1024)  # バイトデータで受信
            if message:
                try:
                    message = message.decode("utf-8")  # バイトデータを文字列にデコード
                    data = json.loads(message)  # JSON形式で受信
                    messages.append(data.get("message", ""))
                except json.JSONDecodeError:
                    messages.append("Error: Invalid JSON received")

                stdscr.clear()  # 画面をクリア

                # メッセージ表示の範囲を指定し、行数を制限
                max_display_lines = curses.LINES - 7
                start_idx = max(0, len(messages) - max_display_lines)
                displayed_messages = messages[start_idx:]

                # メッセージを上から順に表示
                for i, msg in enumerate(displayed_messages):
                    if i < max_display_lines:
                        stdscr.addstr(
                            5 + i, 0, msg[: curses.COLS - 1]
                        )  # メッセージを表示（幅を制限）

                # "You:" とその入力欄を画面の最下部に固定
                stdscr.addstr(curses.LINES - 2, 0, "You: ")  # 画面の最下部に "You:"
                stdscr.refresh()  # 画面を更新
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

    # サーバーに接続
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        client_socket.connect((HOST, PORT))
    except Exception as e:
        stdscr.addstr(f"Error connecting to server: {e}\n")
        stdscr.refresh()
        return

    client_socket.sendall(json.dumps("").encode("utf-8"))

    # ユーザー名の入力プロンプト表示
    stdscr.addstr(0, 0, "Enter your username: ")
    stdscr.refresh()
    stdscr.addstr(1, 0, "> ")  # 改行して次の行で入力を促す
    stdscr.refresh()
    curses.echo()  # 入力内容を表示
    username = stdscr.getstr(1, 3, 20).decode()  # ユーザー名を取得
    curses.noecho()  # 入力表示を終了

    # ユーザー名をサーバーデータベースで検索
    search_user = {"action": "get_user", "user_id": username}
    client_socket.send(json.dumps(search_user).encode("utf-8"))

    isExist = client_socket.recv(1024)

    # 改行してから、ルーム名の入力プロンプト表示
    stdscr.addstr(2, 0, "Enter your password: ")
    stdscr.refresh()
    stdscr.addstr(3, 0, "> ")  # 次の行で入力を促す
    stdscr.refresh()
    curses.echo()  # 入力内容を表示
    password = stdscr.getstr(3, 3, 20).decode()  # ルーム名を取得
    if isExist:
        client_socket.send()
        correct_pass = client_socket.recv(1024)

    curses.noecho()  # 入力表示を終了

    # 改行してから、ルーム名の入力プロンプト表示
    stdscr.addstr(2, 0, "Enter room name: ")
    stdscr.refresh()
    stdscr.addstr(3, 0, "> ")  # 次の行で入力を促す
    stdscr.refresh()
    curses.echo()  # 入力内容を表示
    room = stdscr.getstr(3, 3, 20).decode()  # ルーム名を取得
    curses.noecho()  # 入力表示を終了

    # メッセージ表示領域の管理
    messages = []  # メッセージを保持するリスト
    max_lines = curses.LINES - 7  # "You:"の2行上までメッセージを表示
    stdscr.refresh()

    # 最初に "You entering room" を表示
    entering_room_msg = f"You entering room {room}"

    # メッセージ受信用のスレッドを開始
    threading.Thread(
        target=receive_messages, args=(client_socket, stdscr, messages), daemon=True
    ).start()

    # メッセージ送信ループ
    try:
        while True:
            # メッセージをリストに追加
            stdscr.clear()  # 画面をクリア
            stdscr.addstr(
                4, 0, entering_room_msg
            )  # "You entering room ..." メッセージを最初に表示

            # メッセージを上から順番に表示（最大で "You:" の2行上まで表示）
            for i, message in enumerate(messages):
                if i < curses.LINES - 7:  # "You:" の2行上まで表示
                    stdscr.addstr(
                        5 + i, 0, message[: curses.COLS - 1]
                    )  # メッセージを表示（幅を制限）

            # メッセージが増えて画面がいっぱいになったら、古いメッセージを上に繰り上げる
            if len(messages) + 1 >= max_lines:
                messages.pop(0)  # 古いメッセージを削除

            # "You:" とその入力欄を画面の最下部に固定
            stdscr.addstr(curses.LINES - 2, 0, "You: ")  # 画面の最下部に "You: "
            stdscr.move(curses.LINES - 2, 5)  # 入力カーソルを "You: " の後に移動
            stdscr.refresh()

            curses.echo()  # 入力内容を表示
            msg_content = stdscr.getstr(
                curses.LINES - 2, 5, 100
            ).decode()  # ユーザー入力を取得
            curses.noecho()  # 入力表示を終了

            if msg_content.lower() == "exit":
                stdscr.addstr("\nExiting the chat.\n")
                break

            # メッセージをリストに追加
            messages.append(f"You: {msg_content}")

            # サーバーに送信
            try:
                # メッセージをJSON形式で送信
                message = {"username": username, "room": room, "message": msg_content}
                client_socket.sendall(
                    json.dumps(message).encode("utf-8")  # バイトデータとして送信
                )
            except BrokenPipeError:
                stdscr.addstr("\nConnection lost. Unable to send message.\n")
                stdscr.refresh()
                break

            # 入力欄をリセット
            stdscr.move(curses.LINES - 2, 5)  # 入力欄のカーソル位置をリセット
            stdscr.clrtoeol()  # 入力したメッセージを消去
            stdscr.refresh()

    except KeyboardInterrupt:
        stdscr.addstr("\nDisconnected from server.\n")
    finally:
        client_socket.close()


if __name__ == "__main__":
    curses.wrapper(start_client)
