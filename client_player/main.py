# client_player/main.py

import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from PyQt6.QtWidgets import QApplication
from client_player.network import NetworkClient
from client_dev.ui.login import LoginWindow  # 複用 Developer 的登入畫面！(省事)
from client_player.ui.lobby import LobbyWindow


class PlayerApp:
  def __init__(self):
    self.app = QApplication(sys.argv)
    self.network = NetworkClient()
    self.login_window = None
    self.lobby_window = None

  def start(self):
    # 複用 Dev 的 LoginWindow，它會呼叫 self.network.login
    # 只要我們的 Player NetworkClient 介面跟 Dev NetworkClient 一樣就沒問題
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
  app = PlayerApp()
  app.start()
