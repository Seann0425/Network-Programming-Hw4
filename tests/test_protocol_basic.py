# tests/test_protocol_basic.py

import socket
import threading
import time
import sys
import os

# 將專案根目錄加入 Path，這樣才能 import common
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from common.constants import Command
from common.protocol import send_request, recv_request

# 設定測試用的 Host
TEST_HOST = "127.0.0.1"
TEST_PORT = 9999


def mock_server():
  """模擬一個簡單的 Server，接收資料並回傳確認"""
  server_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
  server_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
  server_sock.bind((TEST_HOST, TEST_PORT))
  server_sock.listen(1)
  print(f"[Server] Listening on {TEST_PORT}...")

  conn, addr = server_sock.accept()
  print(f"[Server] Accepted connection from {addr}")

  # 1. 接收 Client 的登入請求
  cmd, data = recv_request(conn)
  print(f"[Server] Received: Cmd={cmd}, Data={data}")

  # 驗證接收到的資料
  if cmd == Command.LOGIN and data.get("username") == "test_user":
    print("[Server] Data verification PASSED")
    # 2. 回傳成功訊息
    response_data = {"status": "ok", "msg": "Welcome"}
    send_request(conn, Command.LOGIN, response_data)
  else:
    print("[Server] Data verification FAILED")

  conn.close()
  server_sock.close()


def run_test():
  # 啟動 Server Thread
  server_thread = threading.Thread(target=mock_server)
  server_thread.start()

  # 稍微等待 Server 啟動
  time.sleep(0.5)

  # Client 端操作
  client_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
  try:
    client_sock.connect((TEST_HOST, TEST_PORT))

    # 1. 發送測試資料
    payload = {"username": "test_user", "password": "123"}
    print(f"[Client] Sending LOGIN request: {payload}")
    send_request(client_sock, Command.LOGIN, payload)

    # 2. 接收 Server 回應
    cmd, data = recv_request(client_sock)
    print(f"[Client] Received response: Cmd={cmd}, Data={data}")

    # 驗證結果
    if data.get("status") == "ok":
      print("\n>>> Protocol Test SUCCESS! 通訊協定運作正常 <<<")
    else:
      print("\n>>> Protocol Test FAILED! 回應不如預期 <<<")

  except Exception as e:
    print(f"\n>>> Protocol Test ERROR: {e} <<<")
  finally:
    client_sock.close()
    server_thread.join()


if __name__ == "__main__":
  run_test()
