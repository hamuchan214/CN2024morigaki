# コンパイルに使用するコンパイラ
CXX = g++

# ソースコードとヘッダーファイルのディレクトリ
SRC_DIR = server/src
INC_DIR = server/inc

# Boostライブラリのパス
BOOST_INCLUDE = /opt/homebrew/Cellar/boost/1.86.0_2/include  # Boostのインクルードパス
BOOST_LIB = /opt/homebrew/Cellar/boost/1.86.0_2/lib          # Boostのライブラリパス

# 出力ファイル名
OUT = server.out

# コンパイルオプション
CXXFLAGS = -Wall -std=c++17 -I$(INC_DIR) -I$(BOOST_INCLUDE)
LDFLAGS = -L$(BOOST_LIB) -lsqlite3 -lboost_system -pthread

# ソースファイル
SRCS = $(SRC_DIR)/server.cpp $(SRC_DIR)/AsyncDatabase.cpp

# オブジェクトファイル
OBJS = $(SRCS:.cpp=.o)

# デフォルトターゲット
all: $(OUT)

# 最終的な実行ファイルを生成
$(OUT): $(OBJS)
	$(CXX) $(OBJS) -o $(OUT) $(LDFLAGS)

# ソースファイルからオブジェクトファイルを作成
$(SRC_DIR)/%.o: $(SRC_DIR)/%.cpp
	$(CXX) $(CXXFLAGS) -c $< -o $@

# クリーンターゲット
clean:
	rm -f $(OBJS) $(OUT)

.PHONY: all clean
