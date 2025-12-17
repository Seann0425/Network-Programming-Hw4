import sys
import os
import subprocess
import time
import shutil

# 設定預設值 (配合 Server 的起始 Port 30000)
DEFAULT_SERVER_IP = "127.0.0.1"
DEFAULT_SERVER_PORT = "30000"


def clear_screen():
  """清除終端機畫面"""
  os.system("cls" if os.name == "nt" else "clear")


def check_and_install_dependencies():
  """檢查並安裝 PyQt6"""
  print("[System] Checking environment dependencies...")
  try:
    import PyQt6

    print("[System] PyQt6 is already installed.")
  except ImportError:
    print("[System] PyQt6 not found. Installing...")
    try:
      # 使用當前 Python 環境安裝
      subprocess.check_call([sys.executable, "-m", "pip", "install", "PyQt6"])
      print("[System] Installation successful.")
    except subprocess.CalledProcessError:
      print("[Error] Failed to install PyQt6. Please install it manually.")
      sys.exit(1)


def get_connection_info():
  """獲取 Server IP 與 Port"""
  print("\n" + "-" * 40)
  print(" Connection Settings")
  print("-" * 40)

  # 1. IP
  ip = input(f"Enter Server IP (Default: {DEFAULT_SERVER_IP}): ").strip()
  if not ip:
    ip = DEFAULT_SERVER_IP

  # 2. Port
  port = input(f"Enter Server Port (Default: {DEFAULT_SERVER_PORT}): ").strip()
  if not port:
    port = DEFAULT_SERVER_PORT

  return ip, port


def run_module(script_path, args=[]):
  """使用當前 Python 解譯器執行指定腳本"""
  if not os.path.exists(script_path):
    print(f"[Error] File not found: {script_path}")
    print("Please make sure you are running demo.py from the project root.")
    input("Press Enter to continue...")
    return

  # 組合指令: python path/to/script.py arg1 arg2
  cmd = [sys.executable, script_path] + args

  print(f"\n[System] Launching: {' '.join(cmd)}")
  print("--------------------------------------------------")

  try:
    subprocess.run(cmd)
  except KeyboardInterrupt:
    print("\n[System] Process interrupted.")


def clean_system():
  """清理資料庫與暫存檔"""
  print("\n[Warning] This will delete:")
  print("  - gamestore.db")
  print("  - server/storage/*")
  print("  - server/installed_games/*")
  print("  - client_player/downloads/*")

  confirm = input("Are you sure? (y/N): ").strip().lower()
  if confirm == "y":
    try:
      if os.path.exists("gamestore.db"):
        os.remove("gamestore.db")
        print("Removed gamestore.db")

      folders_to_clean = [
        "server/storage",
        "server/installed_games",
        "client_player/downloads",
      ]

      for folder in folders_to_clean:
        if os.path.exists(folder):
          # 這裡保留資料夾但刪除內容，或直接刪除重建
          shutil.rmtree(folder)
          os.makedirs(folder, exist_ok=True)  # 重建空資料夾
          # 補回 .gitkeep 防止 git 追蹤問題 (選用)
          with open(os.path.join(folder, ".gitkeep"), "w") as f:
            pass
          print(f"Cleaned {folder}")

      print("[System] Cleanup complete.")
      time.sleep(1)
    except Exception as e:
      print(f"[Error] Cleanup failed: {e}")
      input("Press Enter to continue...")


def main():
  # 1. 啟動時先檢查環境
  check_and_install_dependencies()

  # 2. 獲取一次連線資訊 (也可以放在迴圈內每次問，但放在外面比較方便)
  target_ip, target_port = get_connection_info()

  while True:
    clear_screen()
    print("=" * 40)
    print("   Game Store System - Demo Console")
    print(f"   Target: {target_ip}:{target_port}")
    print("=" * 40)
    print("1. Start Server (Host)")
    print("2. Start Developer Client (Upload/Manage)")
    print("3. Start Player Client (Play/Lobby)")
    print("4. Clean System Data (Reset DB)")
    print("5. Change IP/Port")
    print("q. Quit")
    print("-" * 40)

    choice = input("Select > ").strip().lower()

    if choice == "1":
      # Server 啟動不需要參數 (它自己會找 Port)
      run_module("server/main.py")
    elif choice == "2":
      # Client 需要 IP 和 Port
      run_module("client_dev/main.py", [target_ip, target_port])
    elif choice == "3":
      # Client 需要 IP 和 Port
      run_module("client_player/main.py", [target_ip, target_port])
    elif choice == "4":
      clean_system()
    elif choice == "5":
      target_ip, target_port = get_connection_info()
    elif choice == "q":
      print("Bye!")
      sys.exit(0)
    else:
      print("Invalid option.")
      time.sleep(0.5)


if __name__ == "__main__":
  try:
    main()
  except KeyboardInterrupt:
    print("\n[System] Exiting...")
    sys.exit(0)
