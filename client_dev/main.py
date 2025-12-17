# client_dev/main.py

import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from PyQt6.QtWidgets import QApplication, QMessageBox
from client_dev.network import NetworkClient
from client_dev.ui.login import LoginWindow
from client_dev.ui.dashboard import DashboardWindow
from common.constants import DEFAULT_PORT  # [Option] 也可以直接 import


class DevApp:
  # [Modify] 預設改為 30000
  def __init__(self, server_ip="127.0.0.1", server_port=DEFAULT_PORT):
    self.app = QApplication(sys.argv)
    self.network = NetworkClient()

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
    self.login_window = LoginWindow(self.network)
    self.login_window.login_success.connect(self.show_dashboard)
    self.login_window.show()
    sys.exit(self.app.exec())

  def show_dashboard(self, username):
    self.login_window.close()
    self.dashboard_window = DashboardWindow(self.network, username)
    self.dashboard_window.show()


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

  client_app = DevApp(target_ip, target_port)
  client_app.start()
