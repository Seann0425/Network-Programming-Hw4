# client_dev/ui/upload_dialog.py

import os
import zipfile
from PyQt6.QtWidgets import (
  QDialog,
  QVBoxLayout,
  QLabel,
  QLineEdit,
  QPushButton,
  QFileDialog,
  QComboBox,
  QMessageBox,
  QTextEdit,
)


class UploadDialog(QDialog):
  def __init__(self, parent, network_client):
    super().__init__(parent)
    self.network = network_client
    self.setWindowTitle("Upload New Game")
    self.setGeometry(200, 200, 400, 500)
    self.selected_folder = None
    self.init_ui()

  def init_ui(self):
    layout = QVBoxLayout()

    layout.addWidget(QLabel("Game Name:"))
    self.name_input = QLineEdit()
    layout.addWidget(self.name_input)

    layout.addWidget(QLabel("Version (e.g. 1.0.0):"))
    self.ver_input = QLineEdit()
    layout.addWidget(self.ver_input)

    layout.addWidget(QLabel("Game Type:"))
    self.type_input = QComboBox()
    self.type_input.addItems(["CLI", "GUI", "Multiplayer"])
    layout.addWidget(self.type_input)

    layout.addWidget(QLabel("Execute Command (e.g. main.py or game.exe):"))
    self.exe_input = QLineEdit()
    self.exe_input.setPlaceholderText("The file to run inside the folder")
    layout.addWidget(self.exe_input)

    layout.addWidget(QLabel("Description:"))
    self.desc_input = QTextEdit()
    layout.addWidget(self.desc_input)

    # File Selection
    self.btn_select = QPushButton("Select Game Folder")
    self.btn_select.clicked.connect(self.select_folder)
    layout.addWidget(self.btn_select)

    self.lbl_path = QLabel("No folder selected")
    layout.addWidget(self.lbl_path)

    # Action Buttons
    self.btn_upload = QPushButton("Upload")
    self.btn_upload.clicked.connect(self.handle_upload)
    self.btn_upload.setEnabled(False)
    layout.addWidget(self.btn_upload)

    self.setLayout(layout)

  def select_folder(self):
    folder = QFileDialog.getExistingDirectory(self, "Select Game Directory")
    if folder:
      self.selected_folder = folder
      self.lbl_path.setText(folder)
      self.btn_upload.setEnabled(True)

  def handle_upload(self):
    name = self.name_input.text()
    version = self.ver_input.text()
    game_type = self.type_input.currentText()
    desc = self.desc_input.toPlainText()
    exe_path = self.exe_input.text()

    if not (name and version and self.selected_folder and exe_path):
      QMessageBox.warning(self, "Error", "Please fill all fields")
      return

    # 1. 壓縮資料夾
    zip_path = "temp_upload.zip"
    try:
      self._zip_folder(self.selected_folder, zip_path)
      file_size = os.path.getsize(zip_path)
    except Exception as e:
      QMessageBox.critical(self, "Zip Error", str(e))
      return

    # 2. 呼叫 Network Client 上傳
    try:
      # 這裡我們需要擴充 Network Client 來支援上傳流程
      # 為了方便，我們直接在這裡調用 network 的 socket，但更好的做法是封裝在 network.py
      success, msg = self.network.upload_game(
        name, version, game_type, desc, exe_path, zip_path, file_size
      )

      if success:
        QMessageBox.information(self, "Success", "Game uploaded successfully!")
        self.accept()
      else:
        QMessageBox.warning(self, "Upload Failed", msg)

    finally:
      # 清理暫存檔
      if os.path.exists(zip_path):
        os.remove(zip_path)

  def _zip_folder(self, folder_path, output_path):
    """將資料夾壓縮成 zip，不包含最外層目錄"""
    with zipfile.ZipFile(output_path, "w", zipfile.ZIP_DEFLATED) as zipf:
      for root, dirs, files in os.walk(folder_path):
        for file in files:
          abs_path = os.path.join(root, file)
          # 計算相對路徑，這樣解壓縮時才不會多一層
          rel_path = os.path.relpath(abs_path, folder_path)
          zipf.write(abs_path, rel_path)
