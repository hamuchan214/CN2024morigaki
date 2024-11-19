#include "AsyncDatabase.hpp"
#include <boost/asio/post.hpp>
#include <iostream>

// コンストラクタ
AsyncDatabase::AsyncDatabase(boost::asio::io_context& io_context, const std::string& db_name)
    : io_context(io_context) {
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
void AsyncDatabase::executeAsync(const std::string& query, std::function<void(std::exception_ptr)> callback) {
    boost::asio::post(io_context, [this, query, callback]() {
        try {
            char* errMsg = nullptr;
            int rc = sqlite3_exec(db, query.c_str(), nullptr, nullptr, &errMsg);
            if (rc != SQLITE_OK) {
                std::string error_message = errMsg ? std::string(errMsg) : "Unknown error";
                sqlite3_free(errMsg);
                throw std::runtime_error("SQLite Error: " + error_message);
            }
            callback(nullptr);
        } catch (...) {
            callback(std::current_exception());
        }
    });
}

// 非同期データ取得
void AsyncDatabase::queryAsync(const std::string& query, std::function<void(std::vector<std::vector<std::string>>, std::exception_ptr)> callback) {
    boost::asio::post(io_context, [this, query, callback]() {
        try {
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
            callback(results, nullptr);
        } catch (...) {
            callback({}, std::current_exception());
        }
    });
}

// データベースの初期セットアップ
void AsyncDatabase::setupDatabase(std::function<void(std::exception_ptr)> callback) {
    boost::asio::post(io_context, [this, callback]() {
        try {
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
                char* errMsg = nullptr;
                int rc = sqlite3_exec(db, query.c_str(), nullptr, nullptr, &errMsg);
                if (rc != SQLITE_OK) {
                    std::string error_message = errMsg ? std::string(errMsg) : "Unknown error";
                    sqlite3_free(errMsg);
                    throw std::runtime_error("SQLite Error: " + error_message);
                }
            }
            callback(nullptr);
        } catch (...) {
            callback(std::current_exception());
        }
    });
}

// 新しいユーザーを追加
void AsyncDatabase::addUserAsync(const std::string& username, const std::string& password, std::function<void(std::exception_ptr)> callback) {
    boost::asio::post(io_context, [this, username, password, callback]() {
        try {
            std::string query = "INSERT INTO User (username, password) VALUES ('" + username + "', '" + password + "');";
            char* errMsg = nullptr;
            int rc = sqlite3_exec(db, query.c_str(), nullptr, nullptr, &errMsg);
            if (rc != SQLITE_OK) {
                std::string error_message = errMsg ? std::string(errMsg) : "Unknown error";
                sqlite3_free(errMsg);
                throw std::runtime_error("SQLite Error: " + error_message);
            }
            callback(nullptr);
        } catch (...) {
            callback(std::current_exception());
        }
    });
}

// ユーザー情報を更新
void AsyncDatabase::updateUserAsync(int user_id, const std::string& new_password, std::function<void(std::exception_ptr)> callback) {
    boost::asio::post(io_context, [this, user_id, new_password, callback]() {
        try {
            std::string query = "UPDATE User SET password = '" + new_password + "' WHERE user_id = " + std::to_string(user_id) + ";";
            char* errMsg = nullptr;
            int rc = sqlite3_exec(db, query.c_str(), nullptr, nullptr, &errMsg);
            if (rc != SQLITE_OK) {
                std::string error_message = errMsg ? std::string(errMsg) : "Unknown error";
                sqlite3_free(errMsg);
                throw std::runtime_error("SQLite Error: " + error_message);
            }
            callback(nullptr);
        } catch (...) {
            callback(std::current_exception());
        }
    });
}

// ユーザーの削除
void AsyncDatabase::deleteUserAsync(int user_id, std::function<void(std::exception_ptr)> callback) {
    boost::asio::post(io_context, [this, user_id, callback]() {
        try {
            std::string query = "DELETE FROM User WHERE user_id = " + std::to_string(user_id) + ";";
            char* errMsg = nullptr;
            int rc = sqlite3_exec(db, query.c_str(), nullptr, nullptr, &errMsg);
            if (rc != SQLITE_OK) {
                std::string error_message = errMsg ? std::string(errMsg) : "Unknown error";
                sqlite3_free(errMsg);
                throw std::runtime_error("SQLite Error: " + error_message);
            }
            callback(nullptr);
        } catch (...) {
            callback(std::current_exception());
        }
    });
}

// ユーザーが参加しているルームの一覧を取得
void AsyncDatabase::getRoomsByUserAsync(int user_id, std::function<void(std::vector<std::vector<std::string>>, std::exception_ptr)> callback) {
    boost::asio::post(io_context, [this, user_id, callback]() {
        try {
            std::vector<std::vector<std::string>> results;
            std::string query = "SELECT Room.room_id, Room.room_name, Room.created_at "
                                "FROM RoomUser "
                                "INNER JOIN Room ON RoomUser.room_id = Room.room_id "
                                "WHERE RoomUser.user_id = " + std::to_string(user_id) + ";";
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
            callback(results, nullptr);
        } catch (...) {
            callback({}, std::current_exception());
        }
    });
}

// ルームのメッセージ履歴を取得
void AsyncDatabase::getMessagesByRoomAsync(int room_id, std::function<void(std::vector<std::vector<std::string>>, std::exception_ptr)> callback) {
    boost::asio::post(io_context, [this, room_id, callback]() {
        try {
            std::vector<std::vector<std::string>> results;
            std::string query = "SELECT Message.message_id, User.username, Message.message, Message.timestamp "
                                "FROM Message "
                                "INNER JOIN User ON Message.user_id = User.user_id "
                                "WHERE Message.room_id = " + std::to_string(room_id) + " "
                                "ORDER BY Message.timestamp ASC;";
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
            callback(results, nullptr);
        } catch (...) {
            callback({}, std::current_exception());
        }
    });
}

// ルームのメンバーを取得
void AsyncDatabase::getRoomMembersAsync(int room_id, std::function<void(std::vector<std::vector<std::string>>, std::exception_ptr)> callback) {
    boost::asio::post(io_context, [this, room_id, callback]() {
        try {
            std::vector<std::vector<std::string>> results;
            std::string query = "SELECT User.user_id, User.username FROM RoomUser "
                                "INNER JOIN User ON RoomUser.user_id = User.user_id "
                                "WHERE RoomUser.room_id = " + std::to_string(room_id) + ";";
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
            callback(results, nullptr);
        } catch (...) {
            callback({}, std::current_exception());
        }
    });
}

// 新しいルームを作成
void AsyncDatabase::createRoomAsync(const std::string& room_name, std::function<void(std::exception_ptr)> callback) {
    boost::asio::post(io_context, [this, room_name, callback]() {
        try {
            std::string query = "INSERT INTO Room (room_name) VALUES ('" + room_name + "');";
            char* errMsg = nullptr;
            int rc = sqlite3_exec(db, query.c_str(), nullptr, nullptr, &errMsg);
            if (rc != SQLITE_OK) {
                std::string error_message = errMsg ? std::string(errMsg) : "Unknown error";
                sqlite3_free(errMsg);
                throw std::runtime_error("SQLite Error: " + error_message);
            }
            callback(nullptr);
        } catch (...) {
            callback(std::current_exception());
        }
    });
}

// ルームを削除
void AsyncDatabase::deleteRoomAsync(int room_id, std::function<void(std::exception_ptr)> callback) {
    boost::asio::post(io_context, [this, room_id, callback]() {
        try {
            std::string query = "DELETE FROM Room WHERE room_id = " + std::to_string(room_id) + ";";
            char* errMsg = nullptr;
            int rc = sqlite3_exec(db, query.c_str(), nullptr, nullptr, &errMsg);
            if (rc != SQLITE_OK) {
                std::string error_message = errMsg ? std::string(errMsg) : "Unknown error";
                sqlite3_free(errMsg);
                throw std::runtime_error("SQLite Error: " + error_message);
            }
            callback(nullptr);
        } catch (...) {
            callback(std::current_exception());
        }
    });
}

// メッセージを送信
void AsyncDatabase::sendMessageAsync(int user_id, int room_id, const std::string& message, std::function<void(std::exception_ptr)> callback) {
    boost::asio::post(io_context, [this, user_id, room_id, message, callback]() {
        try {
            std::string query = "INSERT INTO Message (user_id, room_id, message) VALUES (" + 
                                std::to_string(user_id) + ", " + std::to_string(room_id) + ", '" + message + "');";
            char* errMsg = nullptr;
            int rc = sqlite3_exec(db, query.c_str(), nullptr, nullptr, &errMsg);
            if (rc != SQLITE_OK) {
                std::string error_message = errMsg ? std::string(errMsg) : "Unknown error";
                sqlite3_free(errMsg);
                throw std::runtime_error("SQLite Error: " + error_message);
            }
            callback(nullptr);
        } catch (...) {
            callback(std::current_exception());
        }
    });
}

// ユーザーをルームに追加
void AsyncDatabase::addUserToRoomAsync(int user_id, int room_id, std::function<void(std::exception_ptr)> callback) {
    boost::asio::post(io_context, [this, user_id, room_id, callback]() {
        try {
            std::string query = "INSERT OR IGNORE INTO RoomUser (user_id, room_id, last_read_at) VALUES (" +
                                std::to_string(user_id) + ", " + std::to_string(room_id) + ", datetime('now'));";
            char* errMsg = nullptr;
            int rc = sqlite3_exec(db, query.c_str(), nullptr, nullptr, &errMsg);
            if (rc != SQLITE_OK) {
                std::string error_message = errMsg ? std::string(errMsg) : "Unknown error";
                sqlite3_free(errMsg);
                throw std::runtime_error("SQLite Error: " + error_message);
            }
            callback(nullptr);
        } catch (...) {
            callback(std::current_exception());
        }
    });
}

// ユーザーをルームから削除
void AsyncDatabase::removeUserFromRoomAsync(int user_id, int room_id, std::function<void(std::exception_ptr)> callback) {
    boost::asio::post(io_context, [this, user_id, room_id, callback]() {
        try {
            std::string query = "DELETE FROM RoomUser WHERE user_id = " + std::to_string(user_id) +
                                " AND room_id = " + std::to_string(room_id) + ";";
            char* errMsg = nullptr;
            int rc = sqlite3_exec(db, query.c_str(), nullptr, nullptr, &errMsg);
            if (rc != SQLITE_OK) {
                std::string error_message = errMsg ? std::string(errMsg) : "Unknown error";
                sqlite3_free(errMsg);
                throw std::runtime_error("SQLite Error: " + error_message);
            }
            callback(nullptr);
        } catch (...) {
            callback(std::current_exception());
        }
    });
}

// ルーム内の未読メッセージ数を取得
void AsyncDatabase::getUnreadMessagesCountAsync(int user_id, int room_id, std::function<void(int, std::exception_ptr)> callback) {
    boost::asio::post(io_context, [this, user_id, room_id, callback]() {
        try {
            int count = 0;
            std::string query = "SELECT COUNT(*) FROM Message "
                                "WHERE room_id = " + std::to_string(room_id) +
                                " AND timestamp > (SELECT last_read_at FROM RoomUser WHERE user_id = " +
                                std::to_string(user_id) + " AND room_id = " + std::to_string(room_id) + ");";
            char* errMsg = nullptr;
            auto callbackWrapper = [](void* data, int argc, char** argv, char** azColName) -> int {
                if (argc > 0) {
                    *static_cast<int*>(data) = std::stoi(argv[0]);
                }
                return 0;
            };
            int rc = sqlite3_exec(db, query.c_str(), callbackWrapper, &count, &errMsg);
            if (rc != SQLITE_OK) {
                std::string error_message = errMsg ? std::string(errMsg) : "Unknown error";
                sqlite3_free(errMsg);
                throw std::runtime_error("SQLite Error: " + error_message);
            }
            callback(count, nullptr);
        } catch (...) {
            callback(0, std::current_exception());
        }
    });
}

// 未読メッセージを既読に更新
void AsyncDatabase::markMessagesAsReadAsync(int user_id, int room_id, std::function<void(std::exception_ptr)> callback) {
    boost::asio::post(io_context, [this, user_id, room_id, callback]() {
        try {
            std::string query = "UPDATE RoomUser SET last_read_at = datetime('now') "
                                "WHERE user_id = " + std::to_string(user_id) +
                                " AND room_id = " + std::to_string(room_id) + ";";
            char* errMsg = nullptr;
            int rc = sqlite3_exec(db, query.c_str(), nullptr, nullptr, &errMsg);
            if (rc != SQLITE_OK) {
                std::string error_message = errMsg ? std::string(errMsg) : "Unknown error";
                sqlite3_free(errMsg);
                throw std::runtime_error("SQLite Error: " + error_message);
            }
            callback(nullptr);
        } catch (...) {
            callback(std::current_exception());
        }
    });
}
