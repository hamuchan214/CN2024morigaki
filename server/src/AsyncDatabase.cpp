#include "AsyncDatabase.hpp"
#include <iostream>

// コンストラクタ
AsyncDatabase::AsyncDatabase(const std::string& db_name) {
    int rc = sqlite3_open(db_name.c_str(), &db);
    if (rc != SQLITE_OK) {
        throw std::runtime_error("Failed to open database: " + std::string(sqlite3_errmsg(db)));
    }
}

// デストラクタ
AsyncDatabase::~AsyncDatabase() {
    sqlite3_close(db);
}

// 非同期SQL実行
std::future<void> AsyncDatabase::executeAsync(const std::string& query) {
    return std::async(std::launch::async, [this, query]() {
        char* errMsg = nullptr;
        int rc = sqlite3_exec(db, query.c_str(), nullptr, nullptr, &errMsg);
        if (rc != SQLITE_OK) {
            std::string error_message = errMsg ? std::string(errMsg) : "Unknown error";
            sqlite3_free(errMsg);
            throw std::runtime_error("SQLite Error: " + error_message);
        }
    });
}

// 非同期データ取得
std::future<std::vector<std::vector<std::string>>> AsyncDatabase::queryAsync(const std::string& query) {
    return std::async(std::launch::async, [this, query]() {
        std::vector<std::vector<std::string>> results;
        char* errMsg = nullptr;

        auto callbackWrapper = [](void* data, int argc, char** argv, char** azColName) -> int {
            auto* results = static_cast<std::vector<std::vector<std::string>>*>(data);
            std::vector<std::string> row;

            for (int i = 0; i < argc; i++) {
                row.emplace_back(argv[i] ? argv[i] : "NULL");
            }
            results->emplace_back(std::move(row));
            return 0;
        };

        int rc = sqlite3_exec(db, query.c_str(), callbackWrapper, &results, &errMsg);
        if (rc != SQLITE_OK) {
            std::string error_message = errMsg ? std::string(errMsg) : "Unknown error";
            sqlite3_free(errMsg);
            throw std::runtime_error("SQLite Error: " + error_message);
        }
        return results;
    });
}

// 非同期でユーザーを挿入
std::future<void> AsyncDatabase::insertUser(const std::string& username, const std::string& password) {
    return std::async(std::launch::async, [this, username, password]() {
        std::string query = "INSERT INTO User (username, password) VALUES ('" + username + "', '" + password + "');";
        executeAsync(query).get();
    });
}

// 非同期でメッセージを挿入
std::future<void> AsyncDatabase::insertMessage(int user_id, int room_id, const std::string& message) {
    return std::async(std::launch::async, [this, user_id, room_id, message]() {
        std::string query = "INSERT INTO Message (user_id, room_id, message) VALUES (" +
                            std::to_string(user_id) + ", " +
                            std::to_string(room_id) + ", '" +
                            message + "');";
        executeAsync(query).get();
    });
}

// 非同期で全ユーザー名を取得
std::future<std::vector<std::string>> AsyncDatabase::getAllUsernames() {
    return std::async(std::launch::async, [this]() {
        std::string query = "SELECT username FROM User;";
        auto results = queryAsync(query).get();

        std::vector<std::string> usernames;
        for (const auto& row : results) {
            if (!row.empty()) {
                usernames.emplace_back(row[0]);
            }
        }
        return usernames;
    });
}

// 非同期で指定したユーザー情報を取得
std::future<std::vector<std::vector<std::string>>> AsyncDatabase::getUserByUsername(const std::string& username) {
    return std::async(std::launch::async, [this, username]() {
        std::string query = "SELECT user_id, username, created_at FROM User WHERE username = '" + username + "';";
        return queryAsync(query).get();
    });
}

// 非同期で指定したルームにいるユーザーを取得
std::future<std::vector<std::string>> AsyncDatabase::getUsersInRoom(int room_id) {
    return std::async(std::launch::async, [this, room_id]() {
        std::string query = 
            "SELECT U.username FROM RoomUser RU "
            "JOIN User U ON RU.user_id = U.user_id "
            "WHERE RU.room_id = " + std::to_string(room_id) + ";";
        auto results = queryAsync(query).get();

        std::vector<std::string> usernames;
        for (const auto& row : results) {
            if (!row.empty()) {
                usernames.emplace_back(row[0]);
            }
        }
        return usernames;
    });
}

// 非同期でメッセージ履歴を取得
std::future<std::vector<std::vector<std::string>>> AsyncDatabase::getMessageHistory(int room_id) {
    return std::async(std::launch::async, [this, room_id]() {
        std::string query = 
            "SELECT M.message_id, U.username, M.message, M.timestamp "
            "FROM Message M "
            "JOIN User U ON M.user_id = U.user_id "
            "WHERE M.room_id = " + std::to_string(room_id) + " "
            "ORDER BY M.timestamp ASC;";
        return queryAsync(query).get();
    });
}

// データベースの初期セットアップ
void AsyncDatabase::setupDatabase() {
    const std::vector<std::string> createTableQueries = {
        R"(
            CREATE TABLE IF NOT EXISTS User (
                user_id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL UNIQUE,
                password TEXT NOT NULL,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            );
        )",
        R"(
            CREATE TABLE IF NOT EXISTS Room (
                room_id INTEGER PRIMARY KEY AUTOINCREMENT,
                room_name TEXT NOT NULL UNIQUE,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            );
        )",
        R"(
            CREATE TABLE IF NOT EXISTS Message (
                message_id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                room_id INTEGER NOT NULL,
                message TEXT NOT NULL,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(user_id) REFERENCES User(user_id),
                FOREIGN KEY(room_id) REFERENCES Room(room_id)
            );
        )",
        R"(
            CREATE TABLE IF NOT EXISTS RoomUser (
                user_id INTEGER NOT NULL,
                room_id INTEGER NOT NULL,
                last_read_at DATETIME,
                PRIMARY KEY(user_id, room_id),
                FOREIGN KEY(user_id) REFERENCES User(user_id),
                FOREIGN KEY(room_id) REFERENCES Room(room_id)
            );
        )"
    };

    for (const auto& query : createTableQueries) {
        executeAsync(query).get(); // 同期的に実行
    }
}
