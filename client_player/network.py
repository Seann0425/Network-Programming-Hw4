# client_player/network.py

import socket
import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from common.constants import Command, DEFAULT_HOST, DEFAULT_PORT, Status
from common.protocol import send_request, recv_request, recv_file


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
      return True
    except Exception as e:
      print(f"Connection failed: {e}")
      return False

  def login(self, username, password):
    if not self.is_connected:
      return False, "Not connected"
    # role = 'player'
    send_request(
      self.sock,
      Command.LOGIN,
      {"username": username, "password": password, "role": "player"},
    )
    cmd, res = recv_request(self.sock)
    if res.get("status") == Status.SUCCESS.value:
      self.username = username
      return True, res.get("msg")
    return False, res.get("msg")

  def get_all_games(self):
    """P1: 取得所有遊戲列表"""
    send_request(self.sock, Command.LIST_ALL_GAMES, {})
    cmd, res = recv_request(self.sock)
    return res.get("games", [])

  def download_game(self, game_name, save_dir):
    """P2: 下載遊戲"""
    # 1. 發送下載請求
    send_request(self.sock, Command.DOWNLOAD_GAME, {"name": game_name})

    # 2. 接收回應 (包含版本與檔案大小)
    cmd, res = recv_request(self.sock)
    if res.get("status") != Status.SUCCESS.value:
      return False, res.get("msg")

    version = res.get("version")
    file_size = res.get("file_size")

    # 3. 準備接收檔案
    if not os.path.exists(save_dir):
      os.makedirs(save_dir)

    # 暫存 zip 檔路徑
    zip_path = os.path.join(save_dir, f"{game_name}_{version}.zip")

    try:
      recv_file(self.sock, file_size, zip_path)
      return True, {"version": version, "zip_path": zip_path}
    except Exception as e:
      return False, str(e)

  def disconnect(self):
    if self.sock:
      try:
        send_request(self.sock, Command.LOGOUT, {})
        self.sock.close()
      except:
        pass

  def create_room(self, game_name):
    """發送建立房間請求"""
    payload = {"game_name": game_name}
    send_request(self.sock, Command.CREATE_ROOM, payload)

    cmd, res = recv_request(self.sock)
    if res.get("status") == Status.SUCCESS.value:
      return True, res.get("room_id")
    else:
      return False, res.get("msg")

  def rate_game(self, game_name, rating, comment):
    payload = {"game_name": game_name, "rating": rating, "comment": comment}
    send_request(self.sock, Command.RATE_GAME, payload)

    cmd, res = recv_request(self.sock)
    if res.get("status") == Status.SUCCESS.value:
      return True, res.get("msg")
    return False, res.get("msg")
