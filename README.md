# コンピューターネットワーク課題
## Server
基本はcpp+boostで構成
```
cpp:require<cpp+17
boost:latest version
```

# サーバー ドキュメント

このドキュメントは、C++で書かれたソケットサーバーのコードに関する詳細を提供します。サーバーはBoost.Asioライブラリを使用して非同期で通信を処理し、`AsyncDatabase`クラスとの連携を通じてさまざまな操作を行います。

## 依存関係

このサーバーコードは以下のライブラリに依存しています:

- **Boost.Asio**: 非同期I/O操作を行うためのライブラリ
- **C++11**以上が必要です

## 概要

このサーバーは、複数のクライアントからの要求を非同期で受け取り、以下の操作を行います:

- ユーザー管理（追加、削除、更新）
- ルーム管理（作成、削除）
- メッセージ送信、受信
- ユーザーのルーム参加、退出

各リクエストは非同期的に処理され、処理が完了した結果はクライアントに返されます。

## サーバーの構成

サーバーは2つの主なクラスで構成されています:

### 1. `Session` クラス

`Session`クラスは、各クライアントとの通信を処理します。このクラスは、以下の役割を果たします：

- クライアントからのリクエストを非同期で読み取る
- リクエストに基づいて`AsyncDatabase`クラスのメソッドを呼び出す
- 結果を非同期でクライアントに送信する

#### メソッド

- `start()`: セッションの開始。リクエストの受信を待機します。
- `readRequest()`: クライアントからのリクエストを非同期で受け取ります。
- `processRequest()`: 受け取ったリクエストに基づいて対応する非同期操作を呼び出します。
- `sendResponse()`: 成功またはエラーの結果をクライアントに返します。

### 2. `Server` クラス

`Server`クラスは、クライアントからの接続要求を受け入れ、新しいセッションを開始します。このクラスは、以下の役割を果たします：

- クライアントからの接続要求を待機する
- 接続が確立した際に新しい`Session`を開始する

#### メソッド

- `startAccept()`: 新しいクライアント接続を非同期で受け入れます。

### 3. `AsyncDatabase` クラス

`AsyncDatabase`クラスは、非同期的なデータベース操作を担当します。このクラスには、ユーザー管理、メッセージの取得/送信、ルーム管理のための非同期メソッドが含まれています。例えば、`addUserAsync()`、`sendMessageAsync()`、`getMessagesByRoomAsync()`などがあります。

### 主要な非同期操作

以下はサーバーが処理する主なリクエストです：

- **ユーザー管理**
  - `addUserAsync(username, password)`: ユーザーをデータベースに追加します。
  - `updateUserAsync(user_id, new_password)`: ユーザーのパスワードを更新します。
  - `deleteUserAsync(user_id)`: ユーザーを削除します。
  - `getUserAsync(user_id)`: ユーザー情報を取得します。

- **ルーム管理**
  - `createRoomAsync(room_name)`: 新しいルームを作成します。
  - `deleteRoomAsync(room_id)`: ルームを削除します。

- **メッセージ管理**
  - `sendMessageAsync(user_id, room_id, message)`: メッセージを送信します。
  - `getMessagesByRoomAsync(room_id)`: 指定したルームのメッセージを取得します。

- **ユーザーとルームの管理**
  - `addUserToRoomAsync(user_id, room_id)`: ユーザーをルームに追加します。
  - `removeUserFromRoomAsync(user_id, room_id)`: ユーザーをルームから削除します。
  - `getRoomsByUserAsync(user_id)`: ユーザーが参加しているルームを取得します。
  - `getRoomMembersAsync(room_id)`: ルームのメンバーを取得します。

- **未読メッセージの管理**
  - `getUnreadMessagesCountAsync(user_id, room_id)`: ユーザーが特定のルームで未読のメッセージ数を取得します。
  - `markMessagesAsReadAsync(user_id, room_id)`: ユーザーがルームのメッセージを読んだことをマークします。

## 通信プロトコル

サーバーとクライアントはテキストベースのリクエスト/レスポンス方式で通信します。リクエストは文字列として送信され、サーバーはその内容に基づいて適切な処理を行います。

以下はサポートされるリクエストの例です：

- `create_room`
- `add_user <username>`
- `delete_user <user_id>`
- `send_message <user_id> <room_id> <message>`
- `delete_room <room_id>`
- `update_user <user_id> <new_password>`
- `get_user <user_id>`
- `get_messages <room_id>`
- `get_rooms_by_user <user_id>`
- `get_room_members <room_id>`
- `add_user_to_room <user_id> <room_id>`
- `remove_user_from_room <user_id> <room_id>`
- `get_unread_messages_count <user_id> <room_id>`
- `mark_messages_as_read <user_id> <room_id>`

## エラーハンドリング

サーバーは非同期処理の結果として、エラーが発生した場合には`Error`というレスポンスを送信します。成功した場合は`Success`が返されます。

## コンパイルと実行方法

### 必要なライブラリ

- Boost.Asio
- C++11以上


