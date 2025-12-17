# server/main.py

import socket
import sys
import os

# 確保可以 import common
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from server.client_handler import ClientHandler
from server.db_manager import DBManager
from server.room_manager import RoomManager

# 設定起始 Port 為 30000
START_PORT = 30000


def bind_server(host, start_port, max_attempts=100):
  """
  嘗試綁定 Port，若被佔用則自動 +1 尋找下一個
  """
  for port in range(start_port, start_port + max_attempts):
    # 每次嘗試都建立一個新的 Socket 以保持乾淨
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

    try:
      sock.bind((host, port))
      return sock, port
    except OSError:
      # 如果 Port 被佔用 (Address already in use)，關閉 Socket 並嘗試下一個
      # print(f"[Server] Port {port} is busy, trying next...") #這行可以註解掉避免洗版
      sock.close()
      continue

  # 如果試了 max_attempts 次都失敗
  raise RuntimeError(
    f"Could not bind to any port from {start_port} to {start_port + max_attempts}"
  )


def main():
  # 使用 0.0.0.0 以便讓外部 (助教的 Client) 可以連入
  host = "0.0.0.0"

  try:
    # 1. 自動尋找可用 Port (從 30000 開始)
    server_socket, port = bind_server(host, START_PORT)

    server_socket.listen(5)  # Backlog size

    print(f"========================================")
    print(f" Game Store Server Started ")
    print(f" Listening on {host}:{port}")
    print(f"========================================")
    print(f" [IMPORTANT] Client please connect to Port: {port}")
    print(f"========================================")

    db_manager = DBManager()
    room_manager = RoomManager()

    while True:
      # 2. 等待連線 (Blocking)
      client_sock, addr = server_socket.accept()

      # print(f"[Server] New connection from {addr}")

      # 3. 建立並啟動 Handler Thread
      handler = ClientHandler(client_sock, addr, db_manager, room_manager)
      handler.start()

  except KeyboardInterrupt:
    print("\n[Server] Server shutting down...")
  except Exception as e:
    print(f"[Server] Critical Error: {e}")
  finally:
    if "server_socket" in locals():
      server_socket.close()


if __name__ == "__main__":
  main()
