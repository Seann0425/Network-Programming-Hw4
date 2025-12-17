import os
import zipfile
import subprocess
import sys
from PyQt6.QtWidgets import (
  QMainWindow,
  QWidget,
  QVBoxLayout,
  QHBoxLayout,
  QPushButton,
  QLabel,
  QTableWidget,
  QTableWidgetItem,
  QHeaderView,
  QAbstractItemView,
  QMessageBox,
  QDialog,
  QComboBox,
  QTextEdit,
  QApplication,
)


# === 評分視窗類別 ===
class RateDialog(QDialog):
  def __init__(self, parent, game_name):
    super().__init__(parent)
    self.setWindowTitle(f"Rate Game: {game_name}")
    self.setGeometry(300, 300, 300, 250)

    layout = QVBoxLayout()
    layout.addWidget(QLabel(f"Rating for {game_name}:"))

    self.rating_box = QComboBox()
    self.rating_box.addItems(
      ["5 - Excellent", "4 - Good", "3 - Average", "2 - Poor", "1 - Terrible"]
    )
    layout.addWidget(self.rating_box)

    layout.addWidget(QLabel("Comment:"))
    self.comment_input = QTextEdit()
    layout.addWidget(self.comment_input)

    btn_submit = QPushButton("Submit Review")
    btn_submit.clicked.connect(self.accept)
    layout.addWidget(btn_submit)

    self.setLayout(layout)

  def get_data(self):
    text = self.rating_box.currentText()
    rating = int(text.split(" ")[0])
    return rating, self.comment_input.toPlainText()


# === 主大廳視窗 ===
class LobbyWindow(QMainWindow):
  def __init__(self, network_client, username):
    super().__init__()
    self.network = network_client
    self.username = username
    self.download_base_path = os.path.join("client_player", "downloads", self.username)
    self.init_ui()
    self.refresh_list()

  def init_ui(self):
    self.setWindowTitle(f"Game Store - Player: {self.username}")
    self.setGeometry(100, 100, 900, 600)

    central_widget = QWidget()
    self.setCentralWidget(central_widget)
    layout = QVBoxLayout(central_widget)

    # Header
    header = QHBoxLayout()
    header.addWidget(QLabel(f"Welcome, {self.username}"))
    btn_refresh = QPushButton("Refresh Store")
    btn_refresh.clicked.connect(self.refresh_list)
    header.addWidget(btn_refresh)
    layout.addLayout(header)

    # Game List
    self.table = QTableWidget()
    self.table.setColumnCount(5)
    self.table.setHorizontalHeaderLabels(
      ["Game Name", "Latest Ver", "Type", "Local Ver", "Action"]
    )
    self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
    self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
    self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
    layout.addWidget(self.table)

    # P4: Rate Button (放在 Table 下方)
    btn_rate = QPushButton("Rate Selected Game (P4)")
    btn_rate.clicked.connect(self.open_rate_dialog)
    layout.addWidget(btn_rate)

    # Status Bar
    self.lbl_status = QLabel("Ready")
    layout.addWidget(self.lbl_status)

  def refresh_list(self):
    games = self.network.get_all_games()
    self.table.setRowCount(0)
    self.table.setRowCount(len(games))

    for i, game in enumerate(games):
      name = game["name"]
      server_ver = game["version"]

      self.table.setItem(i, 0, QTableWidgetItem(str(name)))
      self.table.setItem(i, 1, QTableWidgetItem(str(server_ver)))
      self.table.setItem(i, 2, QTableWidgetItem(str(game.get("type", "Unknown"))))

      local_ver = self.check_local_version(name)
      self.table.setItem(
        i, 3, QTableWidgetItem(local_ver if local_ver else "Not Installed")
      )

      btn_action = QPushButton()
      if not local_ver:
        btn_action.setText("Download")
        btn_action.setStyleSheet("background-color: #4CAF50; color: white;")
        btn_action.clicked.connect(lambda checked, n=name: self.download_game(n))
      elif local_ver != server_ver:
        btn_action.setText("Update")
        btn_action.setStyleSheet("background-color: #FF9800; color: white;")
        btn_action.clicked.connect(lambda checked, n=name: self.download_game(n))
      else:
        btn_action.setText("Play")
        btn_action.setStyleSheet("background-color: #2196F3; color: white;")
        btn_action.clicked.connect(lambda checked, n=name: self.start_game(n))

      self.table.setCellWidget(i, 4, btn_action)

  def check_local_version(self, game_name):
    game_dir = os.path.join(self.download_base_path, game_name)
    ver_file = os.path.join(game_dir, "version.txt")
    if os.path.exists(ver_file):
      with open(ver_file, "r") as f:
        return f.read().strip()
    return None

  def download_game(self, game_name):
    self.lbl_status.setText(f"Downloading {game_name}...")
    QApplication.processEvents()

    game_dir = os.path.join(self.download_base_path, game_name)
    success, result = self.network.download_game(game_name, game_dir)

    if success:
      zip_path = result["zip_path"]
      version = result["version"]
      try:
        with zipfile.ZipFile(zip_path, "r") as zip_ref:
          zip_ref.extractall(game_dir)
        with open(os.path.join(game_dir, "version.txt"), "w") as f:
          f.write(version)
        os.remove(zip_path)

        self.lbl_status.setText(f"Installed {game_name} v{version}")
        QMessageBox.information(
          self, "Success", f"{game_name} downloaded successfully!"
        )
        self.refresh_list()
      except Exception as e:
        self.lbl_status.setText("Extraction failed")
        QMessageBox.critical(self, "Error", f"Failed to extract: {e}")
    else:
      self.lbl_status.setText("Download failed")
      QMessageBox.warning(self, "Error", f"Download failed: {result}")

  def start_game(self, game_name):
    """P3: 啟動遊戲 (包含 P3 Create Room 流程)"""
    game_dir = os.path.join(self.download_base_path, game_name)
    exe_path = os.path.join(game_dir, "game.py")

    if not os.path.exists(exe_path):
      QMessageBox.critical(self, "Error", f"Game executable not found:\n{exe_path}")
      return

    self.lbl_status.setText(f"Creating room for {game_name}...")
    QApplication.processEvents()  # 更新 UI

    # 1. 向 Server 請求建立房間
    success, result = self.network.create_room(game_name)
    if not success:
      QMessageBox.warning(self, "Error", f"Failed to create room: {result}")
      self.lbl_status.setText("Room creation failed")
      return

    room_id = result
    print(f"[Lobby] Room created: ID={room_id}")
    self.lbl_status.setText(f"Launching {game_name} (Room {room_id})...")

    try:
      # 2. 啟動遊戲並傳入 Room ID
      if exe_path.endswith(".py"):
        cmd = [sys.executable, "game.py", str(room_id)]
      else:
        cmd = [exe_path, str(room_id)]

      subprocess.Popen(cmd, cwd=game_dir)

    except Exception as e:
      self.lbl_status.setText("Launch failed")
      QMessageBox.critical(self, "Error", f"Failed to start game: {e}")

  def open_rate_dialog(self):
    row = self.table.currentRow()
    if row < 0:
      QMessageBox.warning(self, "Warning", "Please select a game to rate")
      return

    game_name = self.table.item(row, 0).text()

    dialog = RateDialog(self, game_name)
    if dialog.exec():
      rating, comment = dialog.get_data()
      success, msg = self.network.rate_game(game_name, rating, comment)
      if success:
        QMessageBox.information(self, "Success", "Thanks for your feedback!")
      else:
        QMessageBox.warning(self, "Failed", msg)
