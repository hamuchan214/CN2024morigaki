import asyncio
from server import ChatServer

if __name__ == "__main__":
    server = ChatServer()
    try:
        asyncio.run(server.start())
    except KeyboardInterrupt:
        print("Server shutting down.")
