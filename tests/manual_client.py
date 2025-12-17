# tests/manual_client.py
import socket
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from common.constants import Command, DEFAULT_HOST, DEFAULT_PORT
from common.protocol import send_request, recv_request


def test():
  sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
  sock.connect((DEFAULT_HOST, DEFAULT_PORT))

  # 測試登入
  send_request(
    sock, Command.LOGIN, {"username": "neo", "password": "123", "role": "dev"}
  )
  cmd, res = recv_request(sock)
  print(f"Server Response: {res}")

  sock.close()


if __name__ == "__main__":
  test()
