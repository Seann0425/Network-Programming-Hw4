import sys
import os
import subprocess
import time


def install_dependencies():
  """1. 確認環境：檢查並自動安裝 PyQt6"""
  print("[System] Checking environment...")
  try:
    import PyQt6

    print("[System] PyQt6 is already installed.")
  except ImportError:
    print("[System] PyQt6 not found. Installing...")
    try:
      subprocess.check_call([sys.executable, "-m", "pip", "install", "PyQt6"])
      print("[System] Installation successful.")
    except subprocess.CalledProcessError:
      print("[Error] Failed to install PyQt6. Please install it manually.")
      input("Press Enter to exit...")
      sys.exit(1)


def get_server_ip():
  """2. 輸入 IP：獲取 Server IP"""
  print("\n" + "=" * 40)
  default_ip = "127.0.0.1"
  ip = input(f"Enter Server IP (Default: {default_ip}): ").strip()
  if not ip:
    return default_ip
  return ip


def launch_client(script_path, server_ip):
  """3. 自動開啟 Client：傳入 IP 並啟動"""
  if not os.path.exists(script_path):
    print(f"[Error] File not found: {script_path}")
    return

  print(f"[System] Launching {script_path} connecting to {server_ip}...")

  # 使用 sys.executable 確保使用當前的 python 環境
  # 將 IP 作為參數傳給 main.py
  cmd = [sys.executable, script_path, server_ip]

  try:
    subprocess.run(cmd)
  except KeyboardInterrupt:
    pass


def main():
  install_dependencies()

  while True:
    # 清除畫面 (Windows / Unix)
    os.system("cls" if os.name == "nt" else "clear")

    print("=" * 40)
    print("   Game Store - Client Launcher")
    print("=" * 40)

    # 詢問 IP
    target_ip = get_server_ip()

    print("\nWhich client do you want to start?")
    print("1. Player Client (For Playing)")
    print("2. Developer Client (For Uploading)")
    print("q. Quit")

    choice = input("\nSelect > ").strip().lower()

    if choice == "1":
      launch_client("client_player/main.py", target_ip)
    elif choice == "2":
      launch_client("client_dev/main.py", target_ip)
    elif choice == "q":
      break
    else:
      print("Invalid selection.")
      time.sleep(1)


if __name__ == "__main__":
  main()
