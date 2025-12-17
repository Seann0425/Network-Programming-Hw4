# client_player/main.py

import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from PyQt6.QtWidgets import QApplication, QMessageBox
from client_player.network import NetworkClient
from client_dev.ui.login import LoginWindow  # 複用 Developer 的登入畫面
from client_player.ui.lobby import LobbyWindow


class PlayerApp:
  def __init__(self, server_ip="127.0.0.1", server_port=8888):
    self.app = QApplication(sys.argv)
    self.network = NetworkClient()

    # [Fix] 啟動時立刻連線
    print(f"[PlayerApp] Connecting to {server_ip}:{server_port}...")
    if not self.network.connect(server_ip, server_port):
      QMessageBox.critical(
        None,
        "Connection Error",
        f"Could not connect to Server at {server_ip}:{server_port}.\nIs the server running?",
      )
      sys.exit(1)

    self.login_window = None
    self.lobby_window = None

  def start(self):
    # 複用 Dev 的 LoginWindow
    self.login_window = LoginWindow(self.network)
    self.login_window.setWindowTitle("Game Store - Player Login")
    self.login_window.login_success.connect(self.show_lobby)
    self.login_window.show()
    sys.exit(self.app.exec())

  def show_lobby(self, username):
    self.login_window.close()
    self.lobby_window = LobbyWindow(self.network, username)
    self.lobby_window.show()


if __name__ == "__main__":
  # 預設連線資訊
  target_ip = "127.0.0.1"
  target_port = 8888

  # [Fix] 支援從指令列參數讀取 IP (給 launcher.py 用)
  if len(sys.argv) > 1:
    target_ip = sys.argv[1]
    print(f"[Main] Overriding Server IP: {target_ip}")

  app = PlayerApp(target_ip, target_port)
  app.start()
