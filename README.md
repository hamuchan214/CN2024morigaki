# ChatServerドキュメント

## 概要
`ChatServer`は非同期のチャットサーバーを構築するためのPythonクラスです。SQLiteをバックエンドとして使用し、ユーザー管理、チャットルーム管理、メッセージの保存と取得をサポートします。

---

## 必要なモジュール
このクラスを使用するには、以下のモジュールが必要です。

- asyncio
- json
- time
- sqlite3（`AsyncDatabase`が依存）
- colorlog（ログの整形）
- hashlib（パスワードのハッシュ化に依存）
- uuid（セッションID生成に使用）

---

## 機能

### セッション管理
- `create_session(user_id)`  
  ユーザーIDに基づいてセッションを作成します。
  - **入力**: ユーザーID
  - **出力**: セッションID

- `validate_session(session_id)`  
  セッションIDの有効性を確認します。
  - **入力**: セッションID
  - **出力**: ユーザーID（有効な場合）、または`None`（無効な場合）

---

### サーバー起動
- `start()`  
  非同期でサーバーを起動し、クライアントからのリクエストを待機します。

---

### クライアントハンドリング
- `handle_client(reader, writer)`  
  クライアントからの接続を処理し、リクエストを適切なアクションにルーティングします。
  - **入力**: `reader`（クライアントからの入力ストリーム）、`writer`（クライアントへの出力ストリーム）
  - **処理**:
    1. クライアントからJSONリクエストを受信。
    2. アクションに応じてレスポンスを生成。
    3. 必要に応じて全クライアントにブロードキャスト。

---

### データベース操作
`AsyncDatabase`を通じて以下の操作をサポートします。

- `add_user(username, password)`  
  新規ユーザーを追加。
- `login(username, password)`  
  ユーザーのログイン認証。
- `get_rooms_by_user(user_id)`  
  ユーザーが所属するルームを取得。
- `get_messages_by_room(room_id)`  
  指定ルーム内のメッセージを取得。
- `create_room(room_name)`  
  新規チャットルームを作成。
- `save_message(user_id, room_id, message)`  
  メッセージを保存。

---

### メッセージのブロードキャスト
- `broadcast_message(message)`  
  接続中のすべてのクライアントにメッセージを送信します。

---

## 使用例
```python
from chat_server import ChatServer
import asyncio

if __name__ == "__main__":
    chat_server = ChatServer(host='127.0.0.1', port=6001)
    asyncio.run(chat_server.start())
