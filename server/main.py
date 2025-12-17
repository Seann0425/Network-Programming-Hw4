# server/main.py

import socket
import sys
import os

# 確保可以 import common (如果不是以此目錄為 root 執行時需要)
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from common.constants import DEFAULT_HOST, DEFAULT_PORT
from server.client_handler import ClientHandler
from server.db_manager import DBManager
from server.room_manager import RoomManager


def main():
  host = DEFAULT_HOST
  port = DEFAULT_PORT

  # 建立 TCP Socket
  server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

  # 設定 SO_REUSEADDR，避免 Server 重啟時 Port 被佔用
  server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

  db_manager = DBManager()
  room_manager = RoomManager()

  try:
    server_socket.bind((host, port))
    server_socket.listen(5)  # Backlog size
    print(f"========================================")
    print(f" Game Store Server Started ")
    print(f" Listening on {host}:{port}")
    print(f"========================================")

    while True:
      # 1. 等待連線 (Blocking)
      client_sock, addr = server_socket.accept()

      # 2. 建立並啟動 Handler Thread
      handler = ClientHandler(client_sock, addr, db_manager, room_manager)
      handler.start()

      # 注意: 這裡不要 join()，否則會卡住無法接受下一個連線

  except KeyboardInterrupt:
    print("\n[Server] Server shutting down...")
  except Exception as e:
    print(f"[Server] Critical Error: {e}")
  finally:
    server_socket.close()


if __name__ == "__main__":
  main()
