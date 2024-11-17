#include "AsyncDatabase.hpp"
#include <iostream>

int main() {
    try {
        // データベースインスタンスの作成
        AsyncDatabase db("chat_app.db");

        // データベースのセットアップ
        db.setupDatabase();

        // ユーザーを追加
        auto insertFuture = db.executeAsync(R"(
            INSERT INTO User (username, password) VALUES ('Alice', 'password123');
        )");
        insertFuture.get(); // 非同期処理の完了を待つ

        // データ取得
        auto queryFuture = db.queryAsync(R"(
            SELECT * FROM User;
        )");

        // 結果を表示
        auto results = queryFuture.get();
        for (const auto& row : results) {
            for (const auto& col : row) {
                std::cout << col << " ";
            }
            std::cout << std::endl;
        }

    } catch (const std::exception& e) {
        std::cerr << "Error: " << e.what() << std::endl;
    }

    return 0;
}
