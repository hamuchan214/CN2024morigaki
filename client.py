import socket
import threading
import curses
import json
import sys
import asyncio

# Server configuration
HOST = "127.0.0.1"
PORT = 6001


def receive_messages(client_socket, stdscr, messages, room_id, entering_room_msg):
    stdscr.scrollok(True)

    while True:
        try:
            # print("loop")
            message = client_socket.recv(4096)
            print("recieved")
            if message:
                try:
                    message = message.decode("utf-8")
                    data = json.loads(message)
                    print(data)
                    if "action" in data.keys():
                        print(data.get("room_id"))
                        print(room_id)

                        if data.get("room_id") == room_id:
                            print(data.get("message"))
                            messages.append(
                                data.get("user_name") + ": " + data.get("message")
                            )
                except json.JSONDecodeError:
                    messages.append("Error: Invalid JSON received")

                stdscr.clear()
                stdscr.addstr(4, 0, entering_room_msg)
                max_display_lines = curses.LINES - 7
                start_idx = max(0, len(messages) - max_display_lines)
                displayed_messages = messages[start_idx:]

                for i, msg in enumerate(displayed_messages):
                    if i < max_display_lines:
                        stdscr.addstr(5 + i, 0, msg[: curses.COLS - 1])

                stdscr.addstr(curses.LINES - 2, 0, "You: ")
                stdscr.refresh()
            else:
                stdscr.addstr("\nServer has closed the connection.\n")
                client_socket.close()
                break
        except Exception as e:
            stdscr.addstr(f"\nAn error occurred: {e}\n")
            client_socket.close()
            break


async def send_request(action, data, client_socket):
    host = "127.0.0.1"
    port = 6001

    try:
        request = {"action": action, **data}
        client_socket.sendall(json.dumps(request).encode())

        response_data = client_socket.recv(1024)
        response = json.loads(response_data.decode())
        return response
    except Exception as e:
        return {"status": "error", "message": str(e)}


async def start_client(stdscr):
    stdscr.clear()

    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        client_socket.connect((HOST, PORT))
    except Exception as e:
        stdscr.addstr(f"Error connecting to server: {e}\n")
        stdscr.refresh()
        return

    while True:
        stdscr.addstr(0, 0, 'Input "i" or "o" (Login:i/Logon:o):')
        stdscr.addstr(1, 0, "> ")
        stdscr.refresh()
        curses.echo()
        ILoginOLogon = stdscr.getstr(1, 3, 1).decode()
        curses.noecho()

        stdscr.clear()

        if ILoginOLogon == "i":
            stdscr.addstr(0, 0, "LOG IN")
            stdscr.addstr(1, 0, "Enter your username: ")
            stdscr.addstr(2, 0, "> ")
            stdscr.refresh()
            curses.echo()
            username = stdscr.getstr(2, 3, 20).decode()
            curses.noecho()

            stdscr.addstr(3, 0, "Enter your password: ")
            stdscr.addstr(4, 0, "> ")
            stdscr.refresh()
            curses.echo()
            password = stdscr.getstr(4, 3, 20).decode()
            curses.noecho()

            search_user = {"username": username, "password": password}
            result = await send_request("login", search_user, client_socket)
            if result["status"] == "success":
                session_id = result["session_id"]
                stdscr.clear()
                break
            else:
                stdscr.addstr(5, 0, "Login failed. Please try again.")
                stdscr.addstr(6, 0, "Continue? y:n")
                stdscr.addstr(7, 0, "> ")

                stdscr.refresh()
                curses.echo()
                Continue = stdscr.getstr(7, 3, 1).decode()
                curses.noecho()

                if Continue == "y":
                    stdscr.clear()
                else:
                    sys.exit()

        else:
            stdscr.addstr(0, 0, "LOG ON")
            stdscr.addstr(1, 0, "Enter your username: ")
            stdscr.refresh()
            stdscr.addstr(2, 0, "> ")
            stdscr.refresh()
            curses.echo()
            username = stdscr.getstr(2, 3, 20).decode()
            curses.noecho()

            stdscr.addstr(3, 0, "Enter your password: ")
            stdscr.refresh()
            stdscr.addstr(4, 0, "> ")
            stdscr.refresh()
            curses.echo()
            password = stdscr.getstr(4, 3, 20).decode()
            curses.noecho()

            user_data = {"username": username, "password": password}
            add_result = await send_request("add_user", user_data, client_socket)
            print(add_result)
            if add_result["status"] != "success":
                stdscr.addstr(5, 0, "The user exists")
            else:
                login_result = await send_request("login", user_data, client_socket)
                if login_result["status"] == "success":
                    session_id = login_result["session_id"]
                    stdscr.clear()
                    break
                else:
                    stdscr.addstr(5, 0, "Login failed. Please try again.")
            stdscr.addstr(6, 0, "Continue? y:n")
            stdscr.addstr(7, 0, ">")
            stdscr.refresh()
            curses.echo()
            Continue = stdscr.getstr(7, 1, 1).decode()
            if Continue == "y":
                stdscr.clear()
            else:
                sys.exit()

    curses.noecho()

    stdscr.addstr(2, 0, "Enter room name: ")
    stdscr.refresh()
    stdscr.addstr(3, 0, "> ")
    stdscr.refresh()
    curses.echo()
    room = stdscr.getstr(3, 3, 20).decode()
    curses.noecho()

    create_room_data = {"room_name": room, "session_id": session_id}
    room_result = await send_request("create_room", create_room_data, client_socket)
    if room_result["status"] == "success":
        room_id = room_result["room_id"]
        print(f"Room ID: {room_id}")
    else:
        join_result = await send_request("join_room", create_room_data, client_socket)
        if join_result["status"] == "success":
            room_id = join_result["room_id"]
        else:
            print("Failed to create room. Exiting...")
            exit()
    # メッセージ表示領域の管理
    messages = []  # メッセージを保持するリスト
    max_lines = curses.LINES - 7  # "You:"の2行上までメッセージを表示
    stdscr.refresh()

    entering_room_msg = f"You entering room {room}"

    # メッセージ受信用のスレッドを開始
    threading.Thread(
        target=receive_messages,
        args=(client_socket, stdscr, messages, room_id, entering_room_msg),
        daemon=True,
    ).start()

    try:
        while True:
            stdscr.clear()
            stdscr.addstr(4, 0, entering_room_msg)

            for i, message in enumerate(messages):
                if i < curses.LINES - 7:
                    stdscr.addstr(5 + i, 0, message[: curses.COLS - 1])

            if len(messages) + 1 >= max_lines:
                messages.pop(0)

            stdscr.addstr(curses.LINES - 2, 0, "You: ")
            stdscr.move(curses.LINES - 2, 5)
            stdscr.refresh()

            curses.echo()
            msg_content = stdscr.getstr(curses.LINES - 2, 5, 100).decode()
            curses.noecho()

            if msg_content.lower() == "exit":
                stdscr.addstr("\nExiting the chat.\n")
                break

            messages.append(f"You: {msg_content}")

            message = {
                "session_id": session_id,
                "room_id": room_id,
                "message": msg_content,
            }
            message_result = await send_request("add_message", message, client_socket)
            stdscr.move(curses.LINES - 2, 5)
            stdscr.clrtoeol()
            stdscr.refresh()

    except KeyboardInterrupt:
        stdscr.addstr("\nDisconnected from server.\n")
    finally:
        client_socket.close()


def main(stdscr):
    asyncio.run(start_client(stdscr))


if __name__ == "__main__":
    curses.wrapper(main)
