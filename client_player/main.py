# client_player/main.py

import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from PyQt6.QtWidgets import QApplication, QMessageBox
from client_player.network import NetworkClient
from client_dev.ui.login import LoginWindow
from client_player.ui.lobby import LobbyWindow


class PlayerApp:
  # [Modify] 預設改為 30000
  def __init__(self, server_ip="127.0.0.1", server_port=30000):
    self.app = QApplication(sys.argv)
    self.network = NetworkClient()

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
  target_ip = "127.0.0.1"
  target_port = 30000  # [Modify] 預設 30000

  if len(sys.argv) > 1:
    target_ip = sys.argv[1]

  if len(sys.argv) > 2:
    try:
      target_port = int(sys.argv[2])
    except ValueError:
      print(f"[Main] Invalid port {sys.argv[2]}, utilizing default 30000")

  app = PlayerApp(target_ip, target_port)
  app.start()
