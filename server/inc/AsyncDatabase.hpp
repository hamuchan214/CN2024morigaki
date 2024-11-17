#ifndef ASYNC_DATABASE_H
#define ASYNC_DATABASE_H

#include <sqlite3.h>
#include <string>
#include <future>
#include <vector>
#include <stdexcept>

// SQLite操作クラス
class AsyncDatabase {
public:
    // コンストラクタとデストラクタ
    explicit AsyncDatabase(const std::string& db_name);
    ~AsyncDatabase();

    // 非同期SQL実行関数
    std::future<void> executeAsync(const std::string& query);
    std::future<std::vector<std::vector<std::string>>> queryAsync(const std::string& query);

    // 特定のクエリ操作用関数
    std::future<void> insertUser(const std::string& username, const std::string& password);
    std::future<void> insertMessage(int user_id, int room_id, const std::string& message);
    std::future<std::vector<std::string>> getAllUsernames();
    std::future<std::vector<std::vector<std::string>>> getUserByUsername(const std::string& username);
    std::future<std::vector<std::string>> getUsersInRoom(int room_id);
    std::future<std::vector<std::vector<std::string>>> getMessageHistory(int room_id);

    // データベースセットアップ関数
    void setupDatabase();

private:
    sqlite3* db;
};

#endif // ASYNC_DATABASE_H

