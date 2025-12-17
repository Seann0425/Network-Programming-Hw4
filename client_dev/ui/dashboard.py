# client_dev/ui/dashboard.py

import os
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
)
from client_dev.ui.upload_dialog import UploadDialog


class DashboardWindow(QMainWindow):
  def __init__(self, network_client, username):
    super().__init__()
    self.network = network_client
    self.username = username
    self.init_ui()

    # 啟動時自動刷新列表
    self.refresh_list()

  def init_ui(self):
    self.setWindowTitle(f"Dev Console - {self.username}")
    self.setGeometry(100, 100, 900, 600)

    # Central Widget
    central_widget = QWidget()
    self.setCentralWidget(central_widget)

    # Main Layout: HBox (Left Menu + Right Content)
    main_layout = QHBoxLayout(central_widget)

    # --- Left Menu ---
    menu_layout = QVBoxLayout()

    self.btn_upload = QPushButton("Upload Game (D1)")
    self.btn_upload.clicked.connect(self.open_upload_dialog)

    self.btn_update = QPushButton("Update Game (D2)")
    self.btn_update.clicked.connect(self.open_update_dialog)

    self.btn_delete = QPushButton("Delete Game (D3)")
    # self.btn_delete.clicked.connect(self.delete_game) # 預留給 D3

    self.btn_refresh = QPushButton("Refresh List")
    self.btn_refresh.clicked.connect(self.refresh_list)

    menu_layout.addWidget(self.btn_upload)
    menu_layout.addWidget(self.btn_update)
    menu_layout.addWidget(self.btn_delete)
    menu_layout.addWidget(self.btn_refresh)
    menu_layout.addStretch()

    main_layout.addLayout(menu_layout, 1)  # Ratio 1

    # --- Right Content (Game List) ---
    content_layout = QVBoxLayout()

    lbl_title = QLabel("My Published Games")
    lbl_title.setStyleSheet("font-size: 16px; font-weight: bold;")
    content_layout.addWidget(lbl_title)

    self.table = QTableWidget()
    self.table.setColumnCount(4)
    self.table.setHorizontalHeaderLabels(["Name", "Version", "Type", "Status"])
    self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)

    # 設定表格行為：整列選取、不可編輯
    self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
    self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)

    content_layout.addWidget(self.table)

    main_layout.addLayout(content_layout, 4)  # Ratio 4

  def closeEvent(self, event):
    """當視窗關閉時斷線"""
    self.network.disconnect()
    event.accept()

  def refresh_list(self):
    """從 Server 抓取列表並更新表格"""
    # 確保 network.py 中已經有 get_my_games 方法
    games = self.network.get_my_games()
    self.table.setRowCount(0)  # 清空舊資料
    self.table.setRowCount(len(games))

    for i, game in enumerate(games):
      self.table.setItem(i, 0, QTableWidgetItem(str(game["name"])))
      self.table.setItem(i, 1, QTableWidgetItem(str(game["version"])))
      self.table.setItem(i, 2, QTableWidgetItem(str(game.get("type", "Unknown"))))
      self.table.setItem(i, 3, QTableWidgetItem("Published"))

  def open_upload_dialog(self):
    """開啟上架對話框 (標準模式)"""
    dialog = UploadDialog(self, self.network)
    if dialog.exec():
      # 如果上傳成功 (Dialog accepted)，刷新列表
      self.refresh_list()

  def open_update_dialog(self):
    """開啟更新對話框 (修改 UploadDialog 行為)"""
    # 1. 取得目前選取的遊戲
    current_row = self.table.currentRow()
    if current_row < 0:
      QMessageBox.warning(
        self, "Warning", "Please select a game to update from the list."
      )
      return

    game_name = self.table.item(current_row, 0).text()

    # 2. 初始化 Dialog
    dialog = UploadDialog(self, self.network)
    dialog.setWindowTitle(f"Update Game: {game_name}")

    # 鎖定遊戲名稱
    dialog.name_input.setText(game_name)
    dialog.name_input.setDisabled(True)
    dialog.btn_upload.setText("Update")

    # 3. 定義更新邏輯
    def handle_update_patch():
      new_version = dialog.ver_input.text()
      exe_path = dialog.exe_input.text()

      if not (new_version and dialog.selected_folder and exe_path):
        QMessageBox.warning(
          dialog, "Error", "Please fill all fields (Version, Exe, Folder)"
        )
        return

      # 壓縮
      zip_path = "temp_update.zip"
      try:
        # 調用 dialog 內部的 _zip_folder
        dialog._zip_folder(dialog.selected_folder, zip_path)
        file_size = os.path.getsize(zip_path)
      except Exception as e:
        QMessageBox.critical(dialog, "Zip Error", str(e))
        return

      # 呼叫 Network 的 update_game
      try:
        success, msg = self.network.update_game(
          game_name, new_version, exe_path, zip_path, file_size
        )
        if success:
          QMessageBox.information(
            dialog, "Success", f"Game {game_name} updated to v{new_version}!"
          )
          dialog.accept()  # 關閉視窗
        else:
          QMessageBox.warning(dialog, "Update Failed", msg)
      except Exception as e:
        QMessageBox.critical(dialog, "Error", f"An error occurred: {e}")
      finally:
        if os.path.exists(zip_path):
          os.remove(zip_path)

    # === 關鍵修正開始 ===
    # 強制移除原本的訊號連接，並接上新的 Patch 方法
    try:
      dialog.btn_upload.clicked.disconnect()
    except TypeError:
      pass  # 防止若原本沒連接會報錯

    dialog.btn_upload.clicked.connect(handle_update_patch)
    # === 關鍵修正結束 ===

    # 執行 Dialog
    if dialog.exec():
      self.refresh_list()
