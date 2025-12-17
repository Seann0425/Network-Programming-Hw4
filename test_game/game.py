# game.py
import time

print("=========================")
print("   GAME STARTED!   ")
print("=========================")
print("Hello from the Game Process!")

# 讓視窗停留，模擬遊戲執行中
try:
  input("Press Enter to exit the game...")
except EOFError:
  # 防止在某些無 console 環境報錯
  time.sleep(5)
