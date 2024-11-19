import socket
import json
import asyncio

class ChatClient:
    def __init__(self, host='127.0.0.1', port=5000):
        self.host = host
        self.port = port

    async def send_request(self, request):
        """サーバーにリクエストを送信し、レスポンスを受け取る"""
        reader, writer = await asyncio.open_connection(self.host, self.port)

        # サーバーにリクエストを送信
        writer.write(json.dumps(request).encode())
        await writer.drain()

        # サーバーからのレスポンスを受信
        data = await reader.read(1024)
        response = json.loads(data.decode())

        print(f"Received response: {response}")

        # 接続を閉じる
        writer.close()
        await writer.wait_closed()

    async def add_user(self, username, password):
        """ユーザーを追加するリクエストを送信"""
        request = {
            'action': 'add_user',
            'username': username,
            'password': password
        }
        await self.send_request(request)

    async def get_user(self, user_id):
        """ユーザー情報を取得するリクエストを送信"""
        request = {
            'action': 'get_user',
            'user_id': user_id
        }
        await self.send_request(request)

    async def create_room(self, room_name):
        """ルームを作成するリクエストを送信"""
        request = {
            'action': 'create_room',
            'room_name': room_name
        }
        await self.send_request(request)

    async def send_message(self, user_id, room_id, message):
        """メッセージを送信するリクエストを送信"""
        request = {
            'action': 'send_message',
            'user_id': user_id,
            'room_id': room_id,
            'message': message
        }
        await self.send_request(request)

    async def get_rooms_by_user(self, user_id):
        """ユーザーが参加しているルームを取得するリクエストを送信"""
        request = {
            'action': 'get_rooms_by_user',
            'user_id': user_id
        }
        await self.send_request(request)

# クライアントの使用例
async def main():
    client = ChatClient()

    # ユーザーを追加
    await client.add_user('user1', 'password123')

    # ユーザー情報を取得
    await client.get_user(1)

    # ルームを作成
    await client.create_room('Room1')

    # メッセージを送信
    await client.send_message(1, 1, 'Hello, this is a test message.')

    # ユーザーが参加しているルームを取得
    await client.get_rooms_by_user(1)

# メイン関数を実行
if __name__ == "__main__":
    asyncio.run(main())
