# Command Documentation

## 1. Add User
### `action == 'add_user'`
- **Description**: 新規ユーザーを追加します。
- **Parameters**:
  - `username`: 新規ユーザーのユーザー名
  - `password`: 新規ユーザーのパスワード
- **Usage**:
  - ユーザーをデータベースに追加する処理を実行します。
  - **Example**:
    ```json
    {
      "action": "add_user",
      "username": "new_user",
      "password": "password123"
    }
    ```

## 2. Get User
### `action == 'get_user'`
- **Description**: 指定したユーザーIDに対応するユーザー情報を取得します。
- **Parameters**:
  - `user_id`: ユーザーID
- **Usage**:
  - ユーザーIDに基づいてデータベースからユーザー情報を取得します。
  - **Example**:
    ```json
    {
      "action": "get_user",
      "user_id": 1
    }
    ```

## 3. Update User
### `action == 'update_user'`
- **Description**: 既存ユーザーの情報を更新します（主にパスワード変更）。
- **Parameters**:
  - `user_id`: ユーザーID
  - `new_password`: 新しいパスワード
- **Usage**:
  - 指定されたユーザーIDのパスワードを新しいパスワードで更新します。
  - **Example**:
    ```json
    {
      "action": "update_user",
      "user_id": 1,
      "new_password": "new_password123"
    }
    ```

## 4. Delete User
### `action == 'delete_user'`
- **Description**: 指定したユーザーIDに対応するユーザーを削除します。
- **Parameters**:
  - `user_id`: ユーザーID
- **Usage**:
  - 指定されたユーザーIDのユーザーをデータベースから削除します。
  - **Example**:
    ```json
    {
      "action": "delete_user",
      "user_id": 1
    }
    ```

## 5. Create Room
### `action == 'create_room'`
- **Description**: 新しいルームを作成します。
- **Parameters**:
  - `room_name`: 新しいルームの名前
- **Usage**:
  - 新しいルームをデータベースに追加します。
  - **Example**:
    ```json
    {
      "action": "create_room",
      "room_name": "New Chat Room"
    }
    ```

## 6. Get Rooms by User
### `action == 'get_rooms_by_user'`
- **Description**: 指定したユーザーIDに関連するルームの情報を取得します。
- **Parameters**:
  - `user_id`: ユーザーID
- **Usage**:
  - ユーザーが所属しているルームの情報を取得します。
  - **Example**:
    ```json
    {
      "action": "get_rooms_by_user",
      "user_id": 1
    }
    ```

## 7. Get Messages by Room
### `action == 'get_messages_by_room'`
- **Description**: 指定したルームIDに関連するメッセージを取得します。
- **Parameters**:
  - `room_id`: ルームID
- **Usage**:
  - ルーム内のメッセージ履歴を取得します。
  - **Example**:
    ```json
    {
      "action": "get_messages_by_room",
      "room_id": 1
    }
    ```

## 8. Get Room Members
### `action == 'get_room_members'`
- **Description**: 指定したルームIDに関連するルームメンバーを取得します。
- **Parameters**:
  - `room_id`: ルームID
- **Usage**:
  - ルームに所属しているメンバーのリストを取得します。
  - **Example**:
    ```json
    {
      "action": "get_room_members",
      "room_id": 1
    }
    ```

## 9. Send Message
### `action == 'send_message'`
- **Description**: 指定したルームにメッセージを送信します。
- **Parameters**:
  - `user_id`: ユーザーID
  - `room_id`: ルームID
  - `message`: 送信するメッセージの内容
- **Usage**:
  - ユーザーが指定したルームにメッセージを送信します。
  - **Example**:
    ```json
    {
      "action": "send_message",
      "user_id": 1,
      "room_id": 1,
      "message": "Hello, everyone!"
    }
    ```

## 10. Add User to Room
### `action == 'add_user_to_room'`
- **Description**: 指定したユーザーを指定したルームに追加します。
- **Parameters**:
  - `user_id`: ユーザーID
  - `room_id`: ルームID
- **Usage**:
  - ユーザーを指定したルームに追加します。
  - **Example**:
    ```json
    {
      "action": "add_user_to_room",
      "user_id": 1,
      "room_id": 2
    }
    ```

## 11. Remove User from Room
### `action == 'remove_user_from_room'`
- **Description**: 指定したユーザーを指定したルームから削除します。
- **Parameters**:
  - `user_id`: ユーザーID
  - `room_id`: ルームID
- **Usage**:
  - ユーザーを指定したルームから削除します。
  - **Example**:
    ```json
    {
      "action": "remove_user_from_room",
      "user_id": 1,
      "room_id": 2
    }
    ```
