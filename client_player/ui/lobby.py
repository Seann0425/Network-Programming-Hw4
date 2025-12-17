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
  QTabWidget,  # <--- 新增
)


# === 評分視窗類別 (維持不變) ===
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

    # 初始載入資料
    self.refresh_store_list()
    self.refresh_room_list()

  def init_ui(self):
    self.setWindowTitle(f"Game System - Player: {self.username}")
    self.setGeometry(100, 100, 900, 600)

    central_widget = QWidget()
    self.setCentralWidget(central_widget)
    main_layout = QVBoxLayout(central_widget)

    # Header
    header = QHBoxLayout()
    header.addWidget(QLabel(f"Welcome, {self.username}"))
    main_layout.addLayout(header)

    # Tabs
    self.tabs = QTabWidget()
    main_layout.addWidget(self.tabs)

    # Tab 1: Game Store (商城 / 下載 / 建立房間)
    self.tab_store = QWidget()
    self.setup_store_tab()
    self.tabs.addTab(self.tab_store, "Game Store")

    # Tab 2: Lobby (房間列表 / 加入房間)
    self.tab_rooms = QWidget()
    self.setup_rooms_tab()
    self.tabs.addTab(self.tab_rooms, "Lobby (Rooms)")

    # Status Bar
    self.lbl_status = QLabel("Ready")
    main_layout.addWidget(self.lbl_status)

  # ==========================
  # Tab 1: Game Store Logic
  # ==========================
  def setup_store_tab(self):
    layout = QVBoxLayout()

    # Toolbar
    btn_refresh = QPushButton("Refresh Games")
    btn_refresh.clicked.connect(self.refresh_store_list)
    layout.addWidget(btn_refresh)

    # Game Table
    self.store_table = QTableWidget()
    self.store_table.setColumnCount(6)
    self.store_table.setHorizontalHeaderLabels(
      ["Game Name", "Rating", "Latest Ver", "Type", "Local Ver", "Action"]
    )
    self.store_table.horizontalHeader().setSectionResizeMode(
      QHeaderView.ResizeMode.Stretch
    )
    self.store_table.setSelectionBehavior(
      QAbstractItemView.SelectionBehavior.SelectRows
    )
    self.store_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
    layout.addWidget(self.store_table)

    # Rate Button
    btn_rate = QPushButton("Rate Selected Game (P4)")
    btn_rate.clicked.connect(self.open_rate_dialog)
    layout.addWidget(btn_rate)

    self.tab_store.setLayout(layout)

  def refresh_store_list(self):
    games = self.network.get_all_games()
    self.store_table.setRowCount(0)
    self.store_table.setRowCount(len(games))

    for i, game in enumerate(games):
      name = game["name"]
      server_ver = game["version"]
      exe_name = game.get("exe_path", "game.py")

      rating = game.get("rating", 0.0)
      count = game.get("rating_count", 0)
      rating_str = f"{rating} ({count})" if count > 0 else "N/A"

      self.store_table.setItem(i, 0, QTableWidgetItem(str(name)))
      self.store_table.setItem(i, 1, QTableWidgetItem(rating_str))
      self.store_table.setItem(i, 2, QTableWidgetItem(str(server_ver)))
      self.store_table.setItem(i, 3, QTableWidgetItem(str(game.get("type", "Unknown"))))

      local_ver = self.check_local_version(name)
      self.store_table.setItem(
        i, 4, QTableWidgetItem(local_ver if local_ver else "Not Installed")
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
        btn_action.setText("Create Room")  # 明確改名為 Create Room
        btn_action.setStyleSheet("background-color: #2196F3; color: white;")
        btn_action.clicked.connect(
          lambda checked, n=name, e=exe_name: self.create_room_and_play(n, e)
        )

      self.store_table.setCellWidget(i, 5, btn_action)

  # ==========================
  # Tab 2: Rooms Logic (Lobby)
  # ==========================
  def setup_rooms_tab(self):
    layout = QVBoxLayout()

    # Toolbar
    btn_refresh = QPushButton("Refresh Rooms")
    btn_refresh.clicked.connect(self.refresh_room_list)
    layout.addWidget(btn_refresh)

    # Room Table
    self.room_table = QTableWidget()
    self.room_table.setColumnCount(5)
    self.room_table.setHorizontalHeaderLabels(
      ["Room ID", "Game", "Host", "Players", "Action"]
    )
    self.room_table.horizontalHeader().setSectionResizeMode(
      QHeaderView.ResizeMode.Stretch
    )
    self.room_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
    self.room_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
    layout.addWidget(self.room_table)

    self.tab_rooms.setLayout(layout)

  def refresh_room_list(self):
    # 呼叫 Network Client 取得房間列表
    rooms = self.network.get_active_rooms()
    self.room_table.setRowCount(0)
    self.room_table.setRowCount(len(rooms))

    for i, room in enumerate(rooms):
      r_id = room["room_id"]
      game_name = room["game_name"]
      host = room["host"]
      players = room["current_players"]
      port = room["port"]

      self.room_table.setItem(i, 0, QTableWidgetItem(str(r_id)))
      self.room_table.setItem(i, 1, QTableWidgetItem(str(game_name)))
      self.room_table.setItem(i, 2, QTableWidgetItem(str(host)))
      self.room_table.setItem(i, 3, QTableWidgetItem(str(players)))

      btn_join = QPushButton("Join")
      btn_join.setStyleSheet("background-color: #9C27B0; color: white;")
      # 綁定 Join 事件，傳入 room_id, port 和 game_name
      btn_join.clicked.connect(
        lambda checked, rid=r_id, p=port, g=game_name: self.join_room(rid, p, g)
      )
      self.room_table.setCellWidget(i, 4, btn_join)

  # ==========================
  # Shared Helpers & Actions
  # ==========================
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
        self.refresh_store_list()
      except Exception as e:
        self.lbl_status.setText("Extraction failed")
        QMessageBox.critical(self, "Error", f"Failed to extract: {e}")
    else:
      self.lbl_status.setText("Download failed")
      QMessageBox.warning(self, "Error", f"Download failed: {result}")

  def create_room_and_play(self, game_name, exe_name):
    """P3: 建立房間並啟動遊戲 (Host)"""
    game_dir = os.path.join(self.download_base_path, game_name)
    exe_path = self._get_exe_path(game_dir, exe_name)
    if not exe_path:
      return

    self.lbl_status.setText(f"Creating room for {game_name}...")
    QApplication.processEvents()

    # 1. 向 Server 請求建立房間
    success, result = self.network.create_room(game_name)
    if not success:
      QMessageBox.warning(self, "Error", f"Failed to create room: {result}")
      self.lbl_status.setText("Room creation failed")
      return

    room_id = result["room_id"]
    port = result["port"]

    self.lbl_status.setText(f"Launching {game_name} (Host, Room {room_id})...")
    self._launch_process(exe_path, room_id, port, game_dir)

    # 切換到 Lobby Tab 讓玩家看到自己開的房
    self.tabs.setCurrentIndex(1)
    self.refresh_room_list()

  def join_room(self, room_id, port, game_name):
    """P3: 加入房間並啟動遊戲 (Client)"""
    # 1. 檢查遊戲是否已安裝
    if not self.check_local_version(game_name):
      QMessageBox.warning(
        self,
        "Missing Game",
        f"You need to download '{game_name}' from the Store tab first.",
      )
      self.tabs.setCurrentIndex(0)  # 自動切換回商城
      return

    game_dir = os.path.join(self.download_base_path, game_name)
    # 這裡假設 exe_name 是 game.py 或 client.py，需要與 Server 保持一致
    # 因為 Join Room 的封包沒有 exe_name，我們先試著找 default
    exe_path = self._get_exe_path(game_dir, "game.py")
    # 如果找不到 game.py, 試試看 client.py (針對 TicTacToe)
    if not exe_path:
      exe_path = self._get_exe_path(game_dir, "client.py")

    if not exe_path:
      return

    self.lbl_status.setText(f"Joining Room {room_id}...")
    self._launch_process(exe_path, room_id, port, game_dir)

  def _get_exe_path(self, game_dir, exe_name):
    target_exe = exe_name if exe_name else "game.py"
    exe_path = os.path.join(game_dir, target_exe)
    if not os.path.exists(exe_path):
      # Try fallback
      fallback = os.path.join(game_dir, "client.py")
      if os.path.exists(fallback):
        return fallback

      QMessageBox.critical(self, "Error", f"Game executable not found:\n{exe_path}")
      return None
    return exe_path

  def _launch_process(self, exe_path, room_id, port, cwd):
    try:
      # [Fix] 將 exe_path 轉為絕對路徑，避免與 cwd 疊加導致路徑錯誤
      abs_exe_path = os.path.abspath(exe_path)

      if exe_path.endswith(".py"):
        # 使用絕對路徑啟動
        cmd = [sys.executable, abs_exe_path, str(room_id), str(port)]
      else:
        cmd = [abs_exe_path, str(room_id), str(port)]

      print(f"[Lobby] Launching: {cmd} (CWD: {cwd})")

      # 這裡也可以考慮加入 stdout/stderr 捕捉，方便之後除錯
      subprocess.Popen(cmd, cwd=cwd)

    except Exception as e:
      self.lbl_status.setText("Launch failed")
      QMessageBox.critical(self, "Error", f"Failed to start game: {e}")

  def open_rate_dialog(self):
    row = self.store_table.currentRow()
    if row < 0:
      QMessageBox.warning(self, "Warning", "Please select a game to rate")
      return

    game_name = self.store_table.item(row, 0).text()
    dialog = RateDialog(self, game_name)
    if dialog.exec():
      rating, comment = dialog.get_data()
      success, msg = self.network.rate_game(game_name, rating, comment)
      if success:
        QMessageBox.information(self, "Success", "Thanks for your feedback!")
      else:
        QMessageBox.warning(self, "Failed", msg)
