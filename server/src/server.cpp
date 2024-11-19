#include <iostream>
#include <boost/asio.hpp>
#include "AsyncDatabase.hpp"

void handleException(const std::exception_ptr& ex) {
    if (ex) {
        try {
            std::rethrow_exception(ex);
        } catch (const std::exception& e) {
            std::cerr << "Error: " << e.what() << std::endl;
        }
    } else {
        std::cout << "Operation completed successfully." << std::endl;
    }
}

int main() {
    try {
        boost::asio::io_context io_context;

        // データベース初期化
        AsyncDatabase db(io_context, "test_chat.db");

        // データベースセットアップ
        db.setupDatabase([](std::exception_ptr ex) {
            handleException(ex);
        });

        // ルーム作成
        db.createRoomAsync("General", [](std::exception_ptr ex) {
            handleException(ex);
        });

        // メッセージを特定のルームに送信
        db.sendMessageAsync(1, 1, "Hello, this is a test message!", [](std::exception_ptr ex) {
            handleException(ex);
        });

        // ルームのメッセージ取得
        db.getMessagesByRoomAsync(1, [](std::vector<std::vector<std::string>> messages, std::exception_ptr ex) {
            if (ex) {
                handleException(ex);
            } else {
                std::cout << "Messages in Room 1:" << std::endl;
                for (const auto& row : messages) {
                    for (const auto& col : row) {
                        std::cout << col << " ";
                    }
                    std::cout << std::endl;
                }
            }
        });

        // ルームにユーザーを追加
        db.addUserToRoomAsync(1, 1, [](std::exception_ptr ex) {
            handleException(ex);
        });

        // ユーザーのルーム一覧取得
        db.getRoomsByUserAsync(1, [](std::vector<std::vector<std::string>> rooms, std::exception_ptr ex) {
            if (ex) {
                handleException(ex);
            } else {
                std::cout << "Rooms for User 1:" << std::endl;
                for (const auto& row : rooms) {
                    for (const auto& col : row) {
                        std::cout << col << " ";
                    }
                    std::cout << std::endl;
                }
            }
        });

        // 未読メッセージ数を取得
        db.getUnreadMessagesCountAsync(1, 1, [](int count, std::exception_ptr ex) {
            if (ex) {
                handleException(ex);
            } else {
                std::cout << "Unread messages in Room 1 for User 1: " << count << std::endl;
            }
        });

        // メッセージを既読にする
        db.markMessagesAsReadAsync(1, 1, [](std::exception_ptr ex) {
            handleException(ex);
        });

        // ユーザー削除
        db.deleteUserAsync(1, [](std::exception_ptr ex) {
            handleException(ex);
        });

        // 非同期処理の実行
        io_context.run();

    } catch (const std::exception& e) {
        std::cerr << "Exception in main: " << e.what() << std::endl;
    }

    return 0;
}
