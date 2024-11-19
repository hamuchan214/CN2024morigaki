#include <iostream>
#include <string>
#include <boost/asio.hpp>
#include <thread>
#include <memory>
#include <functional>
#include <sstream>
#include "AsyncDatabase.hpp"  // AsyncDatabase.hppをインクルード

using boost::asio::ip::tcp;

// クライアントとの接続を処理するハンドラークラス
class Session : public std::enable_shared_from_this<Session> {
public:
    Session(tcp::socket socket, AsyncDatabase& db)
        : socket_(std::move(socket)), db_(db) {}

    void start() {
        read_request();
    }

private:
    void read_request() {
        auto self(shared_from_this());
        boost::asio::async_read_until(socket_, boost::asio::dynamic_buffer(request_), '\n',
            [this, self](boost::system::error_code ec, std::size_t length) {
                if (!ec) {
                    handle_request();
                } else {
                    std::cerr << "Read error: " << ec.message() << std::endl;
                }
            });
    }

    void handle_request() {
        // リクエストを解析して、適切な非同期関数を呼び出す
        std::string command = request_;
        request_.clear();

        std::string response;
        std::stringstream ss(command);
        std::string command_name;
        ss >> command_name;

        if (command_name == "add_user") {
            std::string username, password;
            ss >> username >> password;
            db_.addUserAsync(username, password, [this](std::exception_ptr ex) {
                if (ex) {
                    send_response("Error adding user");
                } else {
                    send_response("User added successfully");
                }
            });
        } else if (command_name == "update_user") {
            int user_id;
            std::string new_password;
            ss >> user_id >> new_password;
            db_.updateUserAsync(user_id, new_password, [this](std::exception_ptr ex) {
                if (ex) {
                    send_response("Error updating user");
                } else {
                    send_response("User updated successfully");
                }
            });
        } else if (command_name == "get_user") {
            int user_id;
            ss >> user_id;
            db_.getUserAsync(user_id, [this](std::vector<std::string> user_info, std::exception_ptr ex) {
                if (ex) {
                    send_response("Error fetching user");
                } else {
                    send_response("User info: " + join(user_info, ", "));
                }
            });
        } else if (command_name == "create_room") {
            std::string room_name;
            ss >> room_name;
            db_.createRoomAsync(room_name, [this](std::exception_ptr ex) {
                if (ex) {
                    send_response("Error creating room");
                } else {
                    send_response("Room created successfully");
                }
            });
        } else if (command_name == "delete_room") {
            int room_id;
            ss >> room_id;
            db_.deleteRoomAsync(room_id, [this](std::exception_ptr ex) {
                if (ex) {
                    send_response("Error deleting room");
                } else {
                    send_response("Room deleted successfully");
                }
            });
        } else if (command_name == "get_messages_by_room") {
            int room_id;
            ss >> room_id;
            db_.getMessagesByRoomAsync(room_id, [this](std::vector<std::vector<std::string>> messages, std::exception_ptr ex) {
                if (ex) {
                    send_response("Error fetching messages");
                } else {
                    send_response("Messages: " + format_messages(messages));
                }
            });
        } else if (command_name == "get_rooms_by_user") {
            int user_id;
            ss >> user_id;
            db_.getRoomsByUserAsync(user_id, [this](std::vector<std::vector<std::string>> rooms, std::exception_ptr ex) {
                if (ex) {
                    send_response("Error fetching rooms");
                } else {
                    send_response("Rooms: " + format_rooms(rooms));
                }
            });
        } else if (command_name == "get_room_members") {
            int room_id;
            ss >> room_id;
            db_.getRoomMembersAsync(room_id, [this](std::vector<std::vector<std::string>> members, std::exception_ptr ex) {
                if (ex) {
                    send_response("Error fetching room members");
                } else {
                    send_response("Room members: " + format_members(members));
                }
            });
        } else if (command_name == "delete_user") {
            int user_id;
            ss >> user_id;
            db_.deleteUserAsync(user_id, [this](std::exception_ptr ex) {
                if (ex) {
                    send_response("Error deleting user");
                } else {
                    send_response("User deleted successfully");
                }
            });
        } else if (command_name == "send_message") {
            int user_id, room_id;
            std::string message;
            ss >> user_id >> room_id;
            std::getline(ss, message);  // メッセージ部分を読み取る
            db_.sendMessageAsync(user_id, room_id, message, [this](std::exception_ptr ex) {
                if (ex) {
                    send_response("Error sending message");
                } else {
                    send_response("Message sent successfully");
                }
            });
        } else if (command_name == "add_user_to_room") {
            int user_id, room_id;
            ss >> user_id >> room_id;
            db_.addUserToRoomAsync(user_id, room_id, [this](std::exception_ptr ex) {
                if (ex) {
                    send_response("Error adding user to room");
                } else {
                    send_response("User added to room successfully");
                }
            });
        } else if (command_name == "remove_user_from_room") {
            int user_id, room_id;
            ss >> user_id >> room_id;
            db_.removeUserFromRoomAsync(user_id, room_id, [this](std::exception_ptr ex) {
                if (ex) {
                    send_response("Error removing user from room");
                } else {
                    send_response("User removed from room successfully");
                }
            });
        } else if (command_name == "get_unread_messages_count") {
            int user_id, room_id;
            ss >> user_id >> room_id;
            db_.getUnreadMessagesCountAsync(user_id, room_id, [this](int count, std::exception_ptr ex) {
                if (ex) {
                    send_response("Error fetching unread messages count");
                } else {
                    send_response("Unread messages count: " + std::to_string(count));
                }
            });
        } else if (command_name == "mark_messages_as_read") {
            int user_id, room_id;
            ss >> user_id >> room_id;
            db_.markMessagesAsReadAsync(user_id, room_id, [this](std::exception_ptr ex) {
                if (ex) {
                    send_response("Error marking messages as read");
                } else {
                    send_response("Messages marked as read successfully");
                }
            });
        } else {
            send_response("Unknown command");
        }
    }

    void send_response(const std::string& response) {
        auto self(shared_from_this());
        boost::asio::async_write(socket_, boost::asio::buffer(response + "\n"),
            [this, self](boost::system::error_code ec, std::size_t length) {
                if (!ec) {
                    read_request();  // 次のリクエストを受け取る
                } else {
                    std::cerr << "Send error: " << ec.message() << std::endl;
                }
            });
    }

    std::string join(const std::vector<std::string>& vec, const std::string& delimiter) {
        std::string result;
        for (size_t i = 0; i < vec.size(); ++i) {
            result += vec[i];
            if (i != vec.size() - 1) result += delimiter;
        }
        return result;
    }

    std::string format_messages(const std::vector<std::vector<std::string>>& messages) {
        std::stringstream ss;
        for (const auto& message : messages) {
            ss << join(message, ", ") << "\n";
        }
        return ss.str();
    }

    std::string format_rooms(const std::vector<std::vector<std::string>>& rooms) {
        std::stringstream ss;
        for (const auto& room : rooms) {
            ss << join(room, ", ") << "\n";
        }
        return ss.str();
    }

    std::string format_members(const std::vector<std::vector<std::string>>& members) {
        std::stringstream ss;
        for (const auto& member : members) {
            ss << join(member, ", ") << "\n";
        }
        return ss.str();
    }

    tcp::socket socket_;
    AsyncDatabase& db_;
    std::string request_;
};

// サーバークラス
class Server {
public:
    Server(boost::asio::io_context& io_context, short port, AsyncDatabase& db)
        : acceptor_(io_context, tcp::endpoint(tcp::v4(), port)), db_(db) {
        start_accept();
    }

private:
    void start_accept() {
        // 接続を待機し、Sessionをshared_ptrで管理する
        acceptor_.async_accept([this](boost::system::error_code ec, tcp::socket socket) {
            if (!ec) {
                // shared_ptrでSessionを管理
                auto session = std::make_shared<Session>(std::move(socket), db_);
                session->start();
            } else {
                std::cerr << "Accept error: " << ec.message() << std::endl;
            }

            start_accept();  // 次のクライアント接続を待機
        });
    }

    tcp::acceptor acceptor_;
    AsyncDatabase& db_;
};

int main() {
    try {
    boost::asio::io_context io_context;  // io_contextを作成
    std::string db_name = "chottochat.db";  // データベースのファイル名（適切なパスに変更）
    AsyncDatabase db(io_context, db_name);  // 引数を渡してインスタンスを作成
        Server server(io_context, 12345, db);  // ポート12345でサーバー開始

        std::cout << "Server is running on port 12345..." << std::endl;
        io_context.run();  // イベントループを開始
    } catch (const std::exception& e) {
        std::cerr << "Exception: " << e.what() << std::endl;
    }

    return 0;
}
