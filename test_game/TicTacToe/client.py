import socket
import sys


def main():
  # 1. 參數解析 (對應 Lobby 的 subprocess 呼叫格式)
  # cmd = [sys.executable, "client.py", str(room_id), str(port)]
  if len(sys.argv) < 3:
    print("Usage: python client.py <room_id> <port>")
    sys.exit(1)

  room_id = sys.argv[1]
  try:
    port = int(sys.argv[2])
  except ValueError:
    print("Error: Port must be an integer.")
    sys.exit(1)

  host = "127.0.0.1"  # Client 預設連線本地 (或依需求改為 Server IP)

  print(f"--- Tic-Tac-Toe Client ---")
  print(f"Connecting to Room [{room_id}] at {host}:{port}...")

  client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

  try:
    client_socket.connect((host, port))
    print("Connected to server successfully!")

    # 2. 遊戲主迴圈
    while True:
      try:
        # 接收伺服器訊息
        data = client_socket.recv(4096).decode("utf-8")

        # 若 data 為空，代表 Server 斷線或遊戲結束
        if not data:
          print("\n[System] Disconnected from server.")
          break

        # 3. 處理輸入請求 (Protocol Handler)
        if "INPUT_REQ" in data:
          # 移除標記，讓顯示更乾淨
          display_msg = data.replace("INPUT_REQ", "")
          print(display_msg, end="")  # 不換行，直接接輸入提示

          # 讀取玩家輸入
          # 注意：這裡使用標準 input() 造成阻塞，這在 CLI 是正常的
          move = input(" > ")

          # 傳送回 Server
          client_socket.sendall(move.encode("utf-8"))
        else:
          # 純顯示訊息 (例如盤面更新、等待中...)
          print(data)

      except ConnectionResetError:
        print("\n[Error] Connection lost.")
        break
      except KeyboardInterrupt:
        print("\n[System] Exiting...")
        break

  except ConnectionRefusedError:
    print(f"[Error] Could not connect to {host}:{port}. Is the server running?")
  except Exception as e:
    print(f"[Error] Unexpected error: {e}")
  finally:
    client_socket.close()


if __name__ == "__main__":
  main()
