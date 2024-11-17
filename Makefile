# コンパイルに使用するコンパイラ
CXX = g++

# ソースコードとヘッダーファイルのディレクトリ
SRC_DIR = server/src
INC_DIR = server/inc

# 出力ファイル名
OUT = server.out

# コンパイルオプション
CXXFLAGS = -Wall -std=c++17 -I$(INC_DIR)

# ソースファイル
SRCS = $(SRC_DIR)/server.cpp $(SRC_DIR)/AsyncDatabase.cpp

# オブジェクトファイル
OBJS = $(SRCS:.cpp=.o)

# デフォルトターゲット
all: $(OUT)

# 最終的な実行ファイルを生成
$(OUT): $(OBJS)
	$(CXX) $(OBJS) -o $(OUT) -lsqlite3

# ソースファイルからオブジェクトファイルを作成
$(SRC_DIR)/%.o: $(SRC_DIR)/%.cpp
	$(CXX) $(CXXFLAGS) -c $< -o $@

# クリーンターゲット
clean:
	rm -f $(OBJS) $(OUT)

.PHONY: all clean
