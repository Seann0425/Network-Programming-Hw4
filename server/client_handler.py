# server/client_handler.py

import threading
import socket
import os
from common.constants import Command, Status
from common.protocol import recv_request, send_request, recv_file, send_file

STORAGE_DIR = "server/storage"


class ClientHandler(threading.Thread):
  def __init__(
    self, client_sock: socket.socket, client_addr: tuple, db_manager, room_manager=None
  ):
    super().__init__()
    self.client_sock = client_sock
    self.client_addr = client_addr
    self.db_manager = db_manager
    self.room_manager = room_manager
    self.running = True
    self.user = None  # 用來儲存登入後的使用者資訊 (User ID/Name)
    self.role = None

  def run(self):
    """執行緒的主要進入點"""
    print(f"[Server] New connection from {self.client_addr}")

    try:
      while self.running:
        # 1. 接收封包
        cmd, data = recv_request(self.client_sock)

        # 若 cmd 為 None，代表連線斷開
        if cmd is None:
          break

        # 2. 處理指令 (Dispatch)
        self.handle_command(cmd, data)

    except Exception as e:
      print(f"[Server] Error handling client {self.client_addr}: {e}")
    finally:
      self.close_connection()

  def handle_command(self, cmd: Command, data: dict):
    """根據 OpCode 分發請求"""
    print(f"[Server] Received Command: {cmd} from {self.client_addr}")

    # TODO: 之後會在這裡引入 controller 或 service 來處理實際業務邏輯
    # 目前先用簡單的 if-else 框架

    if cmd == Command.LOGIN:
      self._handle_login(data)
    elif cmd == Command.LOGOUT:
      self._handle_logout()
    elif cmd == Command.LIST_ALL_GAMES:
      self._handle_list_all_games()
    elif cmd == Command.UPLOAD_GAME:
      self._handle_upload_game(data)
    elif cmd == Command.LIST_MY_GAMES:
      self._handle_list_my_games()
    elif cmd == Command.UPDATE_GAME:
      self._handle_update_game(data)
    elif cmd == Command.DOWNLOAD_GAME:
      self._handle_download_game(data)
    elif cmd == Command.CREATE_ROOM:
      self._handle_create_room(data)
    elif cmd == Command.RATE_GAME:
      self._handle_rate_game(data)
    else:
      # 未知的指令
      print(f"[Server] Unhandled command: {cmd}")
      send_request(self.client_sock, Command.ERROR, {"msg": "Unknown command"})

  def _handle_login(self, data: dict):
    """處理登入 (目前是 Mock)"""
    username = data.get("username")
    password = data.get("password")
    role = data.get("role", "player")

    if self.db_manager.validate_login(role, username, password):
      self.user = username
      self.role = role
      print(f"[Server] {role} {username} logged in.")
      send_request(
        self.client_sock,
        Command.LOGIN,
        {"status": Status.SUCCESS.value, "msg": "Login successful"},
      )
    else:
      # 嘗試註冊 (Auto-Register for Homework convenience)
      success, msg = self.db_manager.register_user(role, username, password)
      if success:
        self.user = username
        self.role = role
        print(f"[Server] New {role} {username} registered and logged in.")
        send_request(
          self.client_sock,
          Command.LOGIN,
          {
            "status": Status.SUCCESS.value,
            "msg": "Account created and logged in",
          },
        )
      else:
        print(f"[Server] Login failed for {username}: {msg}")
        send_request(
          self.client_sock,
          Command.LOGIN,
          {
            "status": Status.ERR_INVALID_CREDENTIALS.value,
            "msg": "Login failed (Wrong password)",
          },
        )

  def _handle_logout(self):
    print(f"[Server] User {self.user} logged out.")
    self.user = None
    self.running = False  # 結束迴圈，斷開連線

  def _handle_upload_game(self, data: dict):
    """
    D1: 處理遊戲上架
    Flow:
    1. 接收 Metadata (JSON)
    2. 檢查 DB 是否允許上架
    3. 回覆 READY
    4. 接收 File Stream
    5. 更新 DB
    """
    print("[Server Debug] Entering _handle_upload_game")
    game_name = data.get("name")
    version = data.get("version")
    file_size = data.get("file_size")

    # 1. 基本檢查
    if not (game_name and version and file_size):
      print("[Server Debug] Missing fields")
      send_request(self.client_sock, Command.ERROR, {"msg": "Missing fields"})
      return

    print("[Server Debug] Checking storage dir...")
    # 2. 準備儲存路徑
    if not os.path.exists(STORAGE_DIR):
      try:
        os.makedirs(STORAGE_DIR)
        print(f"[Server Debug] Created dir: {STORAGE_DIR}")
      except Exception as e:
        print(f"[Server Error] Failed to create dir: {e}")
        return

    # 檔名格式: name_version.zip (防止檔名衝突)
    safe_filename = f"{game_name}_{version}.zip".replace(" ", "_")
    save_path = os.path.join(STORAGE_DIR, safe_filename)

    # 3. 告訴 Client 可以開始傳了
    send_request(
      self.client_sock,
      Command.UPLOAD_GAME,
      {"status": Status.SUCCESS.value, "msg": "Ready to receive"},
    )

    try:
      print(f"[Server] Receiving file for {game_name} ({file_size} bytes)...")

      # 4. 接收檔案串流
      recv_file(self.client_sock, file_size, save_path)
      print(f"[Server] File received: {save_path}")

      # 5. 更新資料庫
      # 這裡假設 exe_path 是開發者填寫的「解壓縮後的啟動檔路徑」，需存入 DB
      exe_path = data.get("exe_path", "")
      success, msg = self.db_manager.add_game(
        game_name,
        version,
        self.user,
        data.get("description"),
        data.get("type"),
        exe_path,
      )

      if success:
        send_request(
          self.client_sock,
          Command.UPLOAD_GAME,
          {"status": Status.SUCCESS.value, "msg": "Upload complete"},
        )
      else:
        # DB 寫入失敗，刪除檔案
        os.remove(save_path)
        send_request(self.client_sock, Command.ERROR, {"msg": f"DB Error: {msg}"})

    except Exception as e:
      print(f"[Server] Upload failed: {e}")
      send_request(self.client_sock, Command.ERROR, {"msg": str(e)})

  def _handle_list_my_games(self):
    if not self.user:
      send_request(self.client_sock, Command.ERROR, {"msg": "Not logged in"})
      return

    games = self.db_manager.list_my_games(self.user)
    send_request(self.client_sock, Command.LIST_MY_GAMES, {"games": games})

  def _handle_update_game(self, data: dict):
    """
    D2: 更新遊戲流程
    邏輯與 Upload 相似，但會檢查權限並覆蓋檔案
    """
    game_name = data.get("name")
    new_version = data.get("version")
    file_size = data.get("file_size")

    # 1. 權限與存在檢查 (透過 DB Manager 的 update_game_version 預檢，或者直接由 DB update 時擋)
    # 為了流程順暢，我們先確認 Server 準備好接收檔案

    # 檔名更新為新版本
    safe_filename = f"{game_name}_{new_version}.zip".replace(" ", "_")
    save_path = os.path.join(STORAGE_DIR, safe_filename)

    # 2. 回覆 Ready
    send_request(
      self.client_sock,
      Command.UPDATE_GAME,
      {"status": Status.SUCCESS.value, "msg": "Ready to receive update"},
    )

    try:
      print(f"[Server] Receiving update for {game_name}...")
      recv_file(self.client_sock, file_size, save_path)

      # 3. 更新 DB
      # 注意: update_game_version 會檢查 author 是否正確
      new_exe_path = data.get("exe_path")
      success, msg = self.db_manager.update_game_version(
        game_name, self.user, new_version, new_exe_path
      )

      if success:
        send_request(
          self.client_sock,
          Command.UPDATE_GAME,
          {"status": Status.SUCCESS.value, "msg": "Update success"},
        )
      else:
        # 權限不足或遊戲不存在，刪除剛上傳的檔案
        if os.path.exists(save_path):
          os.remove(save_path)
        send_request(self.client_sock, Command.ERROR, {"msg": msg})

    except Exception as e:
      print(f"[Server] Update failed: {e}")
      send_request(self.client_sock, Command.ERROR, {"msg": str(e)})

  def _handle_list_all_games(self):
    """P1: 回傳所有遊戲列表"""
    games = self.db_manager.list_all_games()
    print(f"[Server Debug] DB returned games: {games}")
    send_request(self.client_sock, Command.LIST_ALL_GAMES, {"games": games})

  def _handle_download_game(self, data: dict):
    """P2: 處理玩家下載請求"""
    game_name = data.get("name")

    # 1. 從 DB 查詢遊戲最新版本資訊
    # 我們需要確保 DB Manager 有 get_game_info 方法 (稍後確認 db_manager.py)
    # 這裡假設 list_all_games 回傳的資訊裡包含 version，或者我們直接查 DB

    # 為了簡便，我們直接查 DB 取得版本
    # 注意：這裡假設你 server/db_manager.py 的 list_all_games 已經回傳正確資訊
    # 我們稍微擴充一下邏輯：先查版本 -> 組出檔名 -> 傳送

    conn = self.db_manager._get_conn()
    cursor = conn.cursor()
    cursor.execute("SELECT version FROM games WHERE name = ?", (game_name,))
    row = cursor.fetchone()
    conn.close()

    if not row:
      send_request(self.client_sock, Command.ERROR, {"msg": "Game not found"})
      return

    version = row[0]
    # 根據 D1/D2 的儲存規則，檔名是 name_version.zip
    safe_filename = f"{game_name}_{version}.zip".replace(" ", "_")
    file_path = os.path.join(STORAGE_DIR, safe_filename)

    if not os.path.exists(file_path):
      send_request(
        self.client_sock, Command.ERROR, {"msg": "Game file missing on server"}
      )
      return

    file_size = os.path.getsize(file_path)

    # 2. 告訴 Client 準備接收 (包含版本號，讓 Client 更新本地紀錄)
    send_request(
      self.client_sock,
      Command.DOWNLOAD_GAME,
      {"status": Status.SUCCESS.value, "version": version, "file_size": file_size},
    )

    # 3. 傳送檔案
    try:
      print(f"[Server] Sending {safe_filename} to player...")
      send_file(self.client_sock, file_path)
      # 注意: 下載通常不需要像上傳那樣再做一次 Handshake 確認，
      # 因為 Client 收到 header 知道長度後就會自己讀完。
    except Exception as e:
      print(f"[Server] Download error: {e}")

  def _handle_create_room(self, data: dict):
    """P3: 處理建立房間請求"""
    if not self.user:
      send_request(self.client_sock, Command.ERROR, {"msg": "Please login first"})
      return

    game_name = data.get("game_name")
    if not game_name:
      send_request(self.client_sock, Command.ERROR, {"msg": "Game name required"})
      return

    # 使用 RoomManager 建立房間
    if self.room_manager:
      room_id = self.room_manager.create_room(self.user, game_name)

      # 回傳成功與 Room ID
      send_request(
        self.client_sock,
        Command.CREATE_ROOM,
        {"status": Status.SUCCESS.value, "room_id": room_id, "msg": "Room created"},
      )
    else:
      send_request(self.client_sock, Command.ERROR, {"msg": "Server room error"})

  def close_connection(self):
    """清理資源"""
    print(f"[Server] Closing connection {self.client_addr}")
    try:
      self.client_sock.close()
    except:
      pass

  def _handle_rate_game(self, data: dict):
    """P4: 處理評分請求"""
    if not self.user:
      send_request(self.client_sock, Command.ERROR, {"msg": "Login required"})
      return

    game_name = data.get("game_name")
    rating = data.get("rating")
    comment = data.get("comment")

    # 簡單驗證
    if not (game_name and rating):
      send_request(self.client_sock, Command.ERROR, {"msg": "Missing fields"})
      return

    success, msg = self.db_manager.add_review(
      game_name, self.user, int(rating), comment
    )

    if success:
      send_request(
        self.client_sock,
        Command.RATE_GAME,
        {"status": Status.SUCCESS.value, "msg": "Review saved"},
      )
    else:
      send_request(self.client_sock, Command.ERROR, {"msg": msg})
