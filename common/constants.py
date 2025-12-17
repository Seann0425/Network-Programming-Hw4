from enum import Enum, auto


class Command(Enum):
  # --- Auth ---
  LOGIN = auto()  # 登入
  LOGOUT = auto()  # 登出

  # --- Developer Use Cases ---
  UPLOAD_GAME = auto()  # D1: 上架遊戲
  UPDATE_GAME = auto()  # D2: 更新遊戲
  DELETE_GAME = auto()  # D3: 下架遊戲
  LIST_MY_GAMES = auto()  # 取得開發者自己的遊戲列表

  # --- Player Use Cases ---
  LIST_ALL_GAMES = auto()  # P1: 瀏覽商城
  GET_GAME_INFO = auto()  # P1: 取得詳細資訊
  DOWNLOAD_GAME = auto()  # P2: 下載遊戲
  CREATE_ROOM = auto()  # P3: 建立房間
  JOIN_ROOM = auto()  # P3: 加入房間 (延伸)
  RATE_GAME = auto()  # P4: 評分
  LIST_ROOMS = auto()

  # --- System ---
  ERROR = auto()  # 錯誤訊息


class Status(Enum):
  SUCCESS = 0
  ERR_INVALID_CREDENTIALS = 1  # 帳號密碼錯誤
  ERR_ALREADY_LOGGED_IN = 2  # 重複登入
  ERR_PERMISSION_DENIED = 3  # 權限不足
  ERR_GAME_NOT_FOUND = 4  # 找不到遊戲
  ERR_VERSION_MISMATCH = 5  # 版本不符
  ERR_SERVER_ERROR = 99  # 伺服器內部錯誤


# 定義預設的 Host 和 Port，方便測試
DEFAULT_HOST = "127.0.0.1"
DEFAULT_PORT = 8888
