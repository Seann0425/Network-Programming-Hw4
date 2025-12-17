# client_dev/network.py

import socket
import json
import sys
import os

# 路徑修正 (確保能 import common)
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from common.constants import Command, DEFAULT_HOST, DEFAULT_PORT, Status
from common.protocol import send_request, recv_request, send_file


class NetworkClient:
  def __init__(self):
    self.sock = None
    self.is_connected = False
    self.username = None

  def connect(self, host=DEFAULT_HOST, port=DEFAULT_PORT):
    try:
      self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
      self.sock.connect((host, port))
      self.is_connected = True
      print(f"[Network] Connected to {host}:{port}")
      return True
    except Exception as e:
      print(f"[Network] Connection failed: {e}")
      self.is_connected = False
      return False

  def login(self, username, password):
    if not self.is_connected:
      return False, "Not connected to server"

    # 傳送登入請求 (role='dev')
    payload = {"username": username, "password": password, "role": "dev"}
    send_request(self.sock, Command.LOGIN, payload)

    # 等待回應 (Synchronous wait)
    cmd, res = recv_request(self.sock)

    if cmd == Command.LOGIN and res.get("status") == Status.SUCCESS.value:
      self.username = username
      return True, res.get("msg")
    else:
      return False, res.get("msg", "Unknown error")

  def disconnect(self):
    if self.sock:
      try:
        # 禮貌性通知 Server
        send_request(self.sock, Command.LOGOUT, {})
      except:
        pass
      self.sock.close()
      self.is_connected = False
      print("[Network] Disconnected")

  def upload_game(
    self, name, version, game_type, desc, exe_path, zip_file_path, file_size
  ):
    if not self.is_connected:
      return False, "Not connected"

    # 1. 發送 Metadata
    payload = {
      "name": name,
      "version": version,
      "game_type": game_type,
      "description": desc,
      "exe_path": exe_path,
      "file_size": file_size,
    }
    send_request(self.sock, Command.UPLOAD_GAME, payload)

    # 2. 等待 Server 準備好 (Blocking)
    cmd, res = recv_request(self.sock)
    if cmd != Command.UPLOAD_GAME or res.get("status") != Status.SUCCESS.value:
      return False, res.get("msg", "Server rejected upload")

    # 3. 發送檔案串流
    try:
      print(f"[Network] Sending file {file_size} bytes...")
      send_file(self.sock, zip_file_path)
    except Exception as e:
      return False, f"File transfer error: {e}"

    # 4. 等待最終確認
    cmd, res = recv_request(self.sock)
    if res.get("status") == Status.SUCCESS.value:
      return True, "Upload success"
    else:
      return False, res.get("msg", "Unknown error")

  def get_my_games(self):
    """取得開發者自己的遊戲列表"""
    if not self.is_connected:
      return []

    send_request(self.sock, Command.LIST_MY_GAMES, {})
    cmd, res = recv_request(self.sock)

    if cmd == Command.LIST_MY_GAMES:
      return res.get("games", [])
    return []

  def update_game(self, name, new_version, exe_path, zip_path, file_size):
    """D2: 更新遊戲"""
    if not self.is_connected:
      return False, "Not connected"

    # 1. 發送 Metadata
    payload = {
      "name": name,
      "version": new_version,
      "exe_path": exe_path,
      "file_size": file_size,
    }
    send_request(self.sock, Command.UPDATE_GAME, payload)

    # 2. 等待 Ready (加入超時保護)
    self.sock.settimeout(5.0)
    try:
      cmd, res = recv_request(self.sock)
    except socket.timeout:
      self.sock.settimeout(None)
      return False, "Server timeout"
    except Exception as e:
      self.sock.settimeout(None)
      return False, str(e)

    self.sock.settimeout(None)  # 恢復

    if res.get("status") != Status.SUCCESS.value:
      return False, res.get("msg")

    # 3. 傳送檔案
    try:
      send_file(self.sock, zip_path)
    except Exception as e:
      return False, f"File send error: {e}"

    # 4. 等待結果
    cmd, res = recv_request(self.sock)
    if res.get("status") == Status.SUCCESS.value:
      return True, "Success"
    else:
      return False, res.get("msg")

  def delete_game(self, game_name):
    send_request(self.sock, Command.DELETE_GAME, {"name": game_name})
    cmd, res = recv_request(self.sock)
    if res.get("status") == Status.SUCCESS.value:
      return True, res.get("msg")
    return False, res.get("msg")
