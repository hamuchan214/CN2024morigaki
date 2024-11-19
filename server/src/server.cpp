#include <iostream>
#include <boost/asio.hpp>
#include "AsyncDatabase.hpp"

int main() {
    try {
        // Boost Asio IOコンテキスト
        boost::asio::io_context io_context;

        // データベースインスタンス作成
        AsyncDatabase db(io_context, "test_chat.db");

        // データベースのセットアップ
        db.setupDatabase([](std::exception_ptr ex) {
            if (ex) {
                try {
                    std::rethrow_exception(ex);
                } catch (const std::exception& e) {
                    std::cerr << "Error in setupDatabase: " << e.what() << std::endl;
                }
            } else {
                std::cout << "Database setup completed successfully." << std::endl;
            }
        });

        // サンプルクエリを実行
        db.executeAsync("INSERT INTO User (username, password) VALUES ('user1', 'pass1');", 
            [](std::exception_ptr ex) {
                if (ex) {
                    try {
                        std::rethrow_exception(ex);
                    } catch (const std::exception& e) {
                        std::cerr << "Error in executeAsync: " << e.what() << std::endl;
                    }
                } else {
                    std::cout << "Query executed successfully: User1 added." << std::endl;
                }
            });

        db.executeAsync("INSERT INTO Room (room_name) VALUES ('General');", 
            [](std::exception_ptr ex) {
                if (ex) {
                    try {
                        std::rethrow_exception(ex);
                    } catch (const std::exception& e) {
                        std::cerr << "Error in executeAsync: " << e.what() << std::endl;
                    }
                } else {
                    std::cout << "Query executed successfully: Room added." << std::endl;
                }
            });

        // 非同期操作が完了するまで待機
        io_context.run();
    } catch (const std::exception& e) {
        std::cerr << "Exception in main: " << e.what() << std::endl;
    }

    return 0;
}
