# tictactoe_demo/client.py
import sys
import time

print("==============================")
print("   Tic-Tac-Toe Client v1.0    ")
print("==============================")

# 接收 Player Client 傳進來的參數 (Port, RoomID)
# 參數順序由我們稍後的 Player Client 決定
if len(sys.argv) > 2:
  room_id = sys.argv[1]
  port = sys.argv[2]
  print(f"Connecting to Room {room_id} at port {port}...")
else:
  print("Error: Missing arguments (RoomID, Port)")

# 模擬遊戲畫面
try:
  input("Press Enter to exit game...")
except:
  pass
