# tictactoe_demo/server.py
import argparse
import time
import sys

# 解析 Lobby Server 傳來的參數
parser = argparse.ArgumentParser()
parser.add_argument("--port", type=int, required=True)
parser.add_argument("--room_id", type=str, required=True)
args = parser.parse_args()

print(f"[GameServer] Starting TicTacToe for Room {args.room_id} on Port {args.port}")
sys.stdout.flush()  # 確保 Lobby Server 看得到 log

# 模擬一個簡單的 Socket Server (目前先不做真連線，只要確保能跑起來)
try:
  # 這裡未來會寫 socket bind/listen
  while True:
    time.sleep(1)
except KeyboardInterrupt:
  print("[GameServer] Stopping...")
