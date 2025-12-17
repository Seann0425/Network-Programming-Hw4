# server/room_manager.py

import threading
import random


class RoomManager:
  def __init__(self):
    self.rooms = {}  # {room_id: {'host': username, 'game': game_name, 'players': []}}
    self.lock = threading.Lock()

  def create_room(self, host, game_name):
    """建立房間並回傳 Room ID"""
    with self.lock:
      # 簡單產生一個 4 位數 ID，實務上可用 uuid
      while True:
        room_id = str(random.randint(1000, 9999))
        if room_id not in self.rooms:
          break

      self.rooms[room_id] = {"host": host, "game": game_name, "players": [host]}
      print(f"[RoomMgr] Room {room_id} created by {host} for {game_name}")
      return room_id

  def list_rooms(self):
    """回傳房間列表 (未來做加入房間功能會用到)"""
    with self.lock:
      # 回傳 list of dict
      return [{"id": k, **v} for k, v in self.rooms.items()]
