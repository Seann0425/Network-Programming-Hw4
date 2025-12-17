# client_dev/main.py

import sys
import os

# 路徑修正
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from PyQt6.QtWidgets import QApplication, QMessageBox
from client_dev.network import NetworkClient
from client_dev.ui.login import LoginWindow
from client_dev.ui.dashboard import DashboardWindow


class DevApp:
  def __init__(self, server_ip="127.0.0.1", server_port=8888):
    self.app = QApplication(sys.argv)
    self.network = NetworkClient()

    # [Fix] 啟動時立刻連線，確保 Login 視窗可以使用網路
    print(f"[DevApp] Connecting to {server_ip}:{server_port}...")
    if not self.network.connect(server_ip, server_port):
      QMessageBox.critical(
        None,
        "Connection Error",
        f"Could not connect to Server at {server_ip}:{server_port}.\nIs the server running?",
      )
      sys.exit(1)

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
  # 預設連線資訊
  target_ip = "127.0.0.1"
  target_port = 8888

  # [Fix] 支援從指令列參數讀取 IP (給 launcher.py 用)
  if len(sys.argv) > 1:
    target_ip = sys.argv[1]
    print(f"[Main] Overriding Server IP: {target_ip}")

  client_app = DevApp(target_ip, target_port)
  client_app.start()
