# client_dev/main.py

import sys
import os

# 路徑修正
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from PyQt6.QtWidgets import QApplication
from client_dev.network import NetworkClient
from client_dev.ui.login import LoginWindow
from client_dev.ui.dashboard import DashboardWindow


class DevApp:
  def __init__(self):
    self.app = QApplication(sys.argv)
    self.network = NetworkClient()

    self.login_window = None
    self.dashboard_window = None

  def start(self):
    """啟動流程：顯示登入視窗"""
    self.login_window = LoginWindow(self.network)
    self.login_window.login_success.connect(self.show_dashboard)
    self.login_window.show()

    sys.exit(self.app.exec())

  def show_dashboard(self, username):
    """登入成功後切換到 Dashboard"""
    self.login_window.close()

    self.dashboard_window = DashboardWindow(self.network, username)
    self.dashboard_window.show()


if __name__ == "__main__":
  client_app = DevApp()
  client_app.start()
