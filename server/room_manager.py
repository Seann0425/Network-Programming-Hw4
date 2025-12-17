# server/room_manager.py

import threading
import socket
import subprocess
import sys
import os
import time


class RoomManager:
  def __init__(self, base_game_dir="server/installed_games"):
    self.rooms = {}  # {room_id: {'process': PopenObj, 'port': int, 'host': str, 'game': str}}
    self.lock = threading.Lock()
    self.base_game_dir = base_game_dir

    # 建立存放解壓後遊戲的目錄
    if not os.path.exists(self.base_game_dir):
      os.makedirs(self.base_game_dir)

  def _get_free_port(self):
    """找一個閒置的 Port"""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
      s.bind(("", 0))
      return s.getsockname()[1]

  def create_room(self, host, game_name):
    """啟動遊戲 Server 並回傳 Room ID 與 Port"""
    with self.lock:
      # 1. 檢查 Server 端有沒有這個遊戲的執行檔
      game_server_path = os.path.join(self.base_game_dir, game_name, "server.py")

      if not os.path.exists(game_server_path):
        raise FileNotFoundError(f"Server script not found: {game_server_path}")

      # 2. 分配 ID 與 Port
      import random

      room_id = str(random.randint(1000, 9999))
      port = self._get_free_port()

      # 3. 準備啟動參數
      # 注意：我們會傳入環境變數，確保它能找到 project root (避免 Import Error)
      env = os.environ.copy()
      project_root = os.getcwd()  # 假設你是從專案根目錄執行 main.py
      if "PYTHONPATH" in env:
        env["PYTHONPATH"] = project_root + os.pathsep + env["PYTHONPATH"]
      else:
        env["PYTHONPATH"] = project_root

      cmd = [sys.executable, "server.py", "--port", str(port), "--room_id", room_id]

      print(f"[RoomMgr] Spawning game server for {game_name} on port {port}...")
      print(f"[RoomMgr] CWD: {os.path.dirname(game_server_path)}")
      print(f"[RoomMgr] CMD: {cmd}")

      # 4. 啟動 Game Server (關鍵修改：加入 stderr 捕捉與錯誤檢查)
      try:
        process = subprocess.Popen(
          cmd,
          cwd=os.path.dirname(game_server_path),
          stdout=sys.stdout,  # 讓它的 print 直接顯示在主控台方便看
          stderr=subprocess.PIPE,  # 捕捉錯誤輸出
          env=env,  # 傳入環境變數
          text=True,  # 讓 stderr 讀出來是字串
        )
      except Exception as e:
        print(f"[RoomMgr] Failed to execute subprocess: {e}")
        raise e

      # 5. 健康檢查：給它 0.5 秒，看它是不是立刻就死了
      time.sleep(0.5)
      if process.poll() is not None:
        # 如果 poll() 不是 None，代表已經結束 (Crashed)
        _, stderr_output = process.communicate()
        print(f"!!! [Game Server Crash] !!!")
        print(f"Error Message:\n{stderr_output}")
        print(f"!!!!!!!!!!!!!!!!!!!!!!!!!!!")
        raise RuntimeError(
          f"Game Server crashed immediately. Check console for details."
        )

      # 6. 記錄房間資訊
      self.rooms[room_id] = {
        "host": host,
        "game": game_name,
        "port": port,
        "process": process,
        "players": [host],
      }

      print(f"[RoomMgr] Room {room_id} created successfully.")
      return room_id, port

  def join_room(self, room_id, player_name):
    """加入房間，回傳該房間的 Port"""
    with self.lock:
      if room_id not in self.rooms:
        return None, "Room not found"

      room = self.rooms[room_id]
      # 檢查 Game Server 是否還活著
      if room["process"].poll() is not None:
        del self.rooms[room_id]
        return None, "Game server is dead"

      if player_name not in room["players"]:
        room["players"].append(player_name)

      return room["port"], "Joined"

  def get_game_dir(self, game_name):
    return os.path.join(self.base_game_dir, game_name)
