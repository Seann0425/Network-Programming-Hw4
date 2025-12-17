import sys
import socket
from PyQt6.QtWidgets import (
  QApplication,
  QMainWindow,
  QWidget,
  QVBoxLayout,
  QGridLayout,
  QPushButton,
  QLabel,
  QTextEdit,
  QMessageBox,
)
from PyQt6.QtCore import pyqtSignal, QThread, Qt


# === 網路通訊執行緒 (背景接收 Server 訊息) ===
class NetworkThread(QThread):
  msg_received = pyqtSignal(str)  # 一般訊息
  board_updated = pyqtSignal(str)  # 盤面更新 (格式: X, ,O...)
  input_requested = pyqtSignal()  # 輪到你了
  game_over = pyqtSignal(str)  # 遊戲結束
  connection_error = pyqtSignal(str)  # 連線錯誤

  def __init__(self, host, port):
    super().__init__()
    self.host = host
    self.port = port
    self.socket = None
    self.running = True

  def run(self):
    try:
      # 建立連線
      self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
      self.socket.connect((self.host, self.port))
      self.msg_received.emit(f"Connected to Game Server {self.host}:{self.port}")

      while self.running:
        data = self.socket.recv(4096).decode("utf-8", errors="ignore")
        if not data:
          break

        # 處理黏包問題 (如果 Server 連續送多條訊息)
        # 簡單策略：假設 Server 送來的訊息如果包含多個指令，可能黏在一起
        # 這邊簡化處理，直接檢查關鍵字
        # 更嚴謹的做法是 Server 每條訊息加換行符號，這邊用 splitlines

        # 這裡我們簡單將所有收到內容當作一包，如果包含特定關鍵字就觸發
        # 注意：如果 Server 連續 send 很快，這裡可能會一次收到 "INFO:HiBOARD_DATA:..."
        # 為了穩健，建議 Server 每條 send 後面 sleep 微小時間或用固定分隔符
        # 但在此作業規模下，直接解析最後一個有效指令通常足夠

        if "BOARD_DATA:" in data:
          # 取最後一個 BOARD_DATA
          parts = data.split("BOARD_DATA:")
          last_board = parts[-1].split("INFO")[0].split("INPUT")[0].strip()
          self.board_updated.emit(last_board)

        if "INPUT_REQ" in data:
          self.input_requested.emit()

        if "GAME_OVER:" in data:
          res = data.split("GAME_OVER:")[-1].strip()
          self.game_over.emit(res)

        if "INFO:" in data:
          # 簡單過濾出文字訊息顯示
          clean_msg = (
            data.replace("INFO:", "")
            .replace("BOARD_DATA:", "")
            .replace("INPUT_REQ", "")
          )
          # 只顯示可讀部分
          if len(clean_msg) > 5:  # 避免顯示殘餘符號
            self.msg_received.emit(clean_msg)

    except Exception as e:
      self.connection_error.emit(str(e))
    finally:
      if self.socket:
        self.socket.close()

  def send_move(self, position):
    if self.socket:
      try:
        self.socket.sendall(str(position).encode("utf-8"))
      except Exception as e:
        self.connection_error.emit(str(e))

  def stop(self):
    self.running = False
    if self.socket:
      self.socket.close()


# === GUI 主視窗 ===
class TicTacToeWindow(QMainWindow):
  def __init__(self, room_id, port):
    super().__init__()
    self.setWindowTitle(f"Tic-Tac-Toe GUI (Room {room_id})")
    self.resize(400, 550)

    self.room_id = room_id
    self.port = port
    self.my_turn = False

    self.init_ui()
    self.start_game()

  def init_ui(self):
    central_widget = QWidget()
    self.setCentralWidget(central_widget)
    layout = QVBoxLayout(central_widget)

    # 1. 頂部狀態
    self.status_label = QLabel("Connecting to server...")
    self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
    self.status_label.setStyleSheet("font-size: 18px; font-weight: bold; color: #555;")
    layout.addWidget(self.status_label)

    # 2. 棋盤 (Grid Layout)
    grid_container = QWidget()
    grid_layout = QGridLayout()
    grid_layout.setSpacing(10)
    self.buttons = []

    for i in range(9):
      btn = QPushButton("")
      btn.setFixedSize(90, 90)
      btn.setStyleSheet("""
                QPushButton {
                    font-size: 40px; 
                    font-weight: bold; 
                    background-color: #f0f0f0; 
                    border: 2px solid #ccc; 
                    border-radius: 10px;
                }
                QPushButton:disabled {
                    color: #333;
                }
            """)
      btn.setEnabled(False)  # 初始鎖定
      btn.clicked.connect(lambda checked, idx=i: self.make_move(idx))
      grid_layout.addWidget(btn, i // 3, i % 3)
      self.buttons.append(btn)

    grid_container.setLayout(grid_layout)
    layout.addWidget(grid_container, alignment=Qt.AlignmentFlag.AlignCenter)

    # 3. 底部 Log
    layout.addWidget(QLabel("Game Log:"))
    self.log_area = QTextEdit()
    self.log_area.setReadOnly(True)
    self.log_area.setStyleSheet(
      "background-color: #222; color: #0f0; font-family: Monospace;"
    )
    layout.addWidget(self.log_area)

  def start_game(self):
    # 啟動網路執行緒
    self.network = NetworkThread("127.0.0.1", self.port)
    self.network.msg_received.connect(self.log_msg)
    self.network.board_updated.connect(self.update_board)
    self.network.input_requested.connect(self.enable_input)
    self.network.game_over.connect(self.handle_game_over)
    self.network.connection_error.connect(self.handle_error)
    self.network.start()

  def log_msg(self, msg):
    self.log_area.append(f"> {msg}")
    # 自動捲動到底部
    sb = self.log_area.verticalScrollBar()
    sb.setValue(sb.maximum())

  def update_board(self, board_str):
    # 解析 "X, ,O, ,..."
    cells = board_str.split(",")
    for i, symbol in enumerate(cells):
      if i < 9:
        symbol = symbol.strip()
        self.buttons[i].setText(symbol)

        # 設定顏色
        if symbol == "X":
          self.buttons[i].setStyleSheet(
            "QPushButton { color: #2196F3; font-size: 40px; font-weight: bold; background-color: #E3F2FD; border: 2px solid #2196F3; border-radius: 10px; }"
          )
        elif symbol == "O":
          self.buttons[i].setStyleSheet(
            "QPushButton { color: #F44336; font-size: 40px; font-weight: bold; background-color: #FFEBEE; border: 2px solid #F44336; border-radius: 10px; }"
          )
        else:
          self.buttons[i].setStyleSheet(
            "QPushButton { background-color: #f0f0f0; border: 2px solid #ccc; border-radius: 10px; }"
          )

  def enable_input(self):
    self.my_turn = True
    self.status_label.setText("Your Turn!")
    self.status_label.setStyleSheet(
      "font-size: 18px; font-weight: bold; color: #4CAF50;"
    )

    # 開啟所有空格的按鈕
    for btn in self.buttons:
      if btn.text().strip() == "":
        btn.setEnabled(True)

  def make_move(self, idx):
    if not self.my_turn:
      return

    self.network.send_move(idx)
    self.my_turn = False

    # 鎖定所有按鈕防止重複點擊
    for btn in self.buttons:
      btn.setEnabled(False)

    self.status_label.setText("Waiting for opponent...")
    self.status_label.setStyleSheet(
      "font-size: 18px; font-weight: bold; color: #FF9800;"
    )

  def handle_game_over(self, result):
    self.status_label.setText("Game Over")
    QMessageBox.information(self, "Game Over", f"Result: {result}")
    self.network.stop()
    self.close()

  def handle_error(self, error_msg):
    self.log_area.append(f"[Error] {error_msg}")
    QMessageBox.critical(
      self, "Connection Error", f"Lost connection to server:\n{error_msg}"
    )
    self.close()

  def closeEvent(self, event):
    if hasattr(self, "network"):
      self.network.stop()
    event.accept()


if __name__ == "__main__":
  app = QApplication(sys.argv)

  # 接收參數: client.py <room_id> <port>
  if len(sys.argv) < 3:
    # 本地測試用預設值
    print("Usage: python client.py <room_id> <port>")
    room_id = "TEST"
    port = 12345
  else:
    room_id = sys.argv[1]
    try:
      port = int(sys.argv[2])
    except ValueError:
      print("Port must be an integer")
      sys.exit(1)

  window = TicTacToeWindow(room_id, port)
  window.show()
  sys.exit(app.exec())
