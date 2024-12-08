# API Request JSON Documentation

## 1. Add User
**Action:** `add_user`

### Request JSON
```
{
  "action": "add_user",
  "username": "user123",
  "password": "securepassword"
}
```

### Parameters:
- `action`: 固定値 `"add_user"`
- `username`: ユーザー名（文字列）
- `password`: パスワード（文字列）

---

## 2. Login
**Action:** `login`

### Request JSON
```
{
  "action": "login",
  "username": "user123",
  "password": "securepassword"
}
```

### Parameters:
- `action`: 固定値 `"login"`
- `username`: ユーザー名（文字列）
- `password`: パスワード（文字列）

---

## 3. Get Rooms by User
**Action:** `get_rooms_by_user`

### Request JSON
```
{
  "action": "get_rooms_by_user",
  "user_id": "user123"
}
```

### Parameters:
- `action`: 固定値 `"get_rooms_by_user"`
- `user_id`: ユーザーID（文字列）

---

## 4. Get Messages by Room
**Action:** `get_messages_by_room`

### Request JSON
```
{
  "action": "get_messages_by_room",
  "room_id": "room1"
}
```

### Parameters:
- `action`: 固定値 `"get_messages_by_room"`
- `room_id`: ルームID（文字列）

---

## 5. Add Message
**Action:** `add_message`

### Request JSON
```
{
  "action": "add_message",
  "session_id": "session123",
  "room_id": "room1",
  "message": "Hello, World!"
}
```

### Parameters:
- `action`: 固定値 `"add_message"`
- `session_id`: セッションID（文字列）
- `room_id`: ルームID（文字列）
- `message`: メッセージ（文字列）

---

## 6. Create Room
**Action:** `create_room`

### Request JSON
```
{
  "action": "create_room",
  "session_id": "session123",
  "room_name": "new_room"
}
```

### Parameters:
- `action`: 固定値 `"create_room"`
- `session_id`: セッションID（文字列）
- `room_name`: 作成するルーム名（文字列）

---

## 7. Get Room Members
**Action:** `get_room_members`

### Request JSON
```
{
  "action": "get_room_members",
  "room_id": "room1"
}
```

### Parameters:
- `action`: 固定値 `"get_room_members"`
- `room_id`: ルームID（文字列）

---

## 8. Add User to Room
**Action:** `join_room`

### Request JSON
```
{
  "action": "join_room",
  "room_id": "room1",
  "user_id": "user123"
}
```

### Parameters:
- `action`: 固定値 `"join_room"`
- `room_id`: ルームID（文字列）
- `user_id`: ユーザーID（文字列）