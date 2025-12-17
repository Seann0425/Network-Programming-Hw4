# client_dev/ui/login.py

from PyQt6.QtWidgets import (
  QWidget,
  QVBoxLayout,
  QLabel,
  QLineEdit,
  QPushButton,
  QMessageBox,
)
from PyQt6.QtCore import pyqtSignal


class LoginWindow(QWidget):
  # 定義訊號: 當登入成功時發出，並傳遞 username
  login_success = pyqtSignal(str)

  def __init__(self, network_client):
    super().__init__()
    self.network = network_client
    self.init_ui()

  def init_ui(self):
    self.setWindowTitle("Game Store - Developer Login")
    self.setGeometry(100, 100, 300, 200)

    layout = QVBoxLayout()

    # Title
    title = QLabel("Developer Console")
    title.setStyleSheet("font-size: 18px; font-weight: bold; margin-bottom: 10px;")
    layout.addWidget(title)

    # Username
    self.user_input = QLineEdit()
    self.user_input.setPlaceholderText("Username")
    layout.addWidget(self.user_input)

    # Password
    self.pass_input = QLineEdit()
    self.pass_input.setPlaceholderText("Password")
    self.pass_input.setEchoMode(QLineEdit.EchoMode.Password)
    layout.addWidget(self.pass_input)

    # Login Button
    self.btn_login = QPushButton("Login / Register")
    self.btn_login.clicked.connect(self.handle_login)
    layout.addWidget(self.btn_login)

    self.setLayout(layout)

  def handle_login(self):
    username = self.user_input.text().strip()
    password = self.pass_input.text().strip()

    if not username or not password:
      QMessageBox.warning(self, "Error", "Please enter username and password")
      return

    # 嘗試連線 (若尚未連線)
    if not self.network.is_connected:
      if not self.network.connect():
        QMessageBox.critical(self, "Connection Error", "Cannot connect to server")
        return

    # 執行登入
    success, msg = self.network.login(username, password)
    if success:
      QMessageBox.information(self, "Success", f"Welcome, {username}!")
      self.login_success.emit(username)  # 發出訊號切換視窗
    else:
      QMessageBox.warning(self, "Login Failed", f"Error: {msg}")
