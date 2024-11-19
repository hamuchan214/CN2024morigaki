#ifndef ASYNC_DATABASE_H
#define ASYNC_DATABASE_H

#include <sqlite3.h>
#include <boost/asio.hpp>
#include <string>
#include <vector>
#include <stdexcept>
#include <memory>
#include <functional>

// SQLite操作クラス
class AsyncDatabase {
public:
    // コンストラクタとデストラクタ
    AsyncDatabase(boost::asio::io_context& io_context, const std::string& db_name);
    ~AsyncDatabase();

    // 非同期SQL実行関数
    void executeAsync(const std::string& query, std::function<void(std::exception_ptr)> callback);
    void queryAsync(const std::string& query, std::function<void(std::vector<std::vector<std::string>>, std::exception_ptr)> callback);

    // データベースセットアップ関数
    void setupDatabase(std::function<void(std::exception_ptr)> callback);

    // その他のクエリ関数
    void addUserAsync(const std::string& username, const std::string& password, std::function<void(std::exception_ptr)> callback);
    void updateUserAsync(int user_id, const std::string& new_password, std::function<void(std::exception_ptr)> callback);
    void getUserAsync(int user_id, std::function<void(std::vector<std::string>, std::exception_ptr)> callback);
    void createRoomAsync(const std::string& room_name, std::function<void(std::exception_ptr)> callback);
    void deleteRoomAsync(int room_id, std::function<void(std::exception_ptr)> callback);
    void getMessagesByRoomAsync(int room_id, std::function<void(std::vector<std::vector<std::string>>, std::exception_ptr)> callback);
    void getRoomsByUserAsync(int user_id, std::function<void(std::vector<std::vector<std::string>>, std::exception_ptr)> callback);
    void getRoomMembersAsync(int room_id, std::function<void(std::vector<std::vector<std::string>>, std::exception_ptr)> callback);
    void deleteUserAsync(int user_id, std::function<void(std::exception_ptr)> callback);
    void sendMessageAsync(int user_id, int room_id, const std::string& message, std::function<void(std::exception_ptr)> callback);
    void addUserToRoomAsync(int user_id, int room_id, std::function<void(std::exception_ptr)> callback);
    void removeUserFromRoomAsync(int user_id, int room_id, std::function<void(std::exception_ptr)> callback);
    void getUnreadMessagesCountAsync(int user_id, int room_id, std::function<void(int, std::exception_ptr)> callback);
    void markMessagesAsReadAsync(int user_id, int room_id, std::function<void(std::exception_ptr)> callback);

private:
    sqlite3* db;
    boost::asio::io_context& io_context;
};

#endif // ASYNC_DATABASE_H

