# server/db_manager.py

import sqlite3
import threading
import hashlib
import os

DB_PATH = "gamestore.db"


class DBManager:
  def __init__(self, db_path=DB_PATH):
    self.db_path = db_path
    self.lock = threading.Lock()
    self._init_tables()

  def _get_conn(self):
    """取得資料庫連線 (每個執行緒獨立連線)"""
    return sqlite3.connect(self.db_path)

  def _hash_password(self, password):
    """簡單的密碼雜湊"""
    return hashlib.sha256(password.encode()).hexdigest()

  def _init_tables(self):
    """初始化資料表"""
    create_developers_table = """
        CREATE TABLE IF NOT EXISTS developers (
            username TEXT PRIMARY KEY,
            password_hash TEXT NOT NULL
        );
        """

    create_players_table = """
        CREATE TABLE IF NOT EXISTS players (
            username TEXT PRIMARY KEY,
            password_hash TEXT NOT NULL
        );
        """

    # 遊戲表：包含名稱、版本、作者、路徑、描述、類型
    create_games_table = """
        CREATE TABLE IF NOT EXISTS games (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            version TEXT NOT NULL,
            author TEXT NOT NULL,
            description TEXT,
            game_type TEXT,
            exe_path TEXT,
            UNIQUE(name)
        );
        """

    create_reviews_table = """
        CREATE TABLE IF NOT EXISTS reviews (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            game_name TEXT NOT NULL,
            player_name TEXT NOT NULL,
            rating INTEGER CHECK(rating >= 1 AND rating <= 5),
            comment TEXT,
            UNIQUE(game_name, player_name)
        );
        """

    with self.lock:
      conn = self._get_conn()
      cursor = conn.cursor()
      cursor.execute(create_developers_table)
      cursor.execute(create_players_table)
      cursor.execute(create_games_table)
      cursor.execute(create_reviews_table)
      conn.commit()
      conn.close()
      print("[DB] Database initialized.")

  # --- User Management ---

  def register_user(self, role, username, password):
    """註冊使用者 (role: 'dev' or 'player')"""
    table = "developers" if role == "dev" else "players"
    pwd_hash = self._hash_password(password)

    with self.lock:
      conn = self._get_conn()
      cursor = conn.cursor()
      try:
        cursor.execute(
          f"INSERT INTO {table} (username, password_hash) VALUES (?, ?)",
          (username, pwd_hash),
        )
        conn.commit()
        return True, "Registration successful"
      except sqlite3.IntegrityError:
        return False, "Username already exists"
      except Exception as e:
        return False, str(e)
      finally:
        conn.close()

  def validate_login(self, role, username, password):
    """驗證登入 (role: 'dev' or 'player')"""
    table = "developers" if role == "dev" else "players"
    pwd_hash = self._hash_password(password)

    with self.lock:
      conn = self._get_conn()
      cursor = conn.cursor()
      cursor.execute(
        f"SELECT password_hash FROM {table} WHERE username = ?", (username,)
      )
      row = cursor.fetchone()
      conn.close()

      if row and row[0] == pwd_hash:
        return True
      return False

  # --- Game Management (Developer Use Cases) ---

  def add_game(self, name, version, author, description, game_type, exe_path):
    """D1: 上架新遊戲"""
    with self.lock:
      conn = self._get_conn()
      cursor = conn.cursor()
      try:
        cursor.execute(
          """
                    INSERT INTO games (name, version, author, description, game_type, exe_path)
                    VALUES (?, ?, ?, ?, ?, ?)
                """,
          (name, version, author, description, game_type, exe_path),
        )
        conn.commit()
        return True, "Game uploaded successfully"
      except sqlite3.IntegrityError:
        return False, "Game name already exists"
      except Exception as e:
        return False, str(e)
      finally:
        conn.close()

  def update_game_version(self, name, author, new_version, new_exe_path):
    """D2: 更新遊戲版本 (需檢查作者權限)"""
    with self.lock:
      conn = self._get_conn()
      cursor = conn.cursor()

      # 1. 檢查遊戲是否存在且作者是否正確
      cursor.execute("SELECT author FROM games WHERE name = ?", (name,))
      row = cursor.fetchone()
      if not row:
        conn.close()
        return False, "Game not found"
      if row[0] != author:
        conn.close()
        return False, "Permission denied: You are not the author"

      # 2. 更新
      cursor.execute(
        """
                UPDATE games 
                SET version = ?, exe_path = ?
                WHERE name = ?
            """,
        (new_version, new_exe_path, name),
      )
      conn.commit()
      conn.close()
      return True, "Game updated successfully"

  def list_all_games(self):
    """P1: 列出所有遊戲"""
    with self.lock:
      conn = self._get_conn()
      cursor = conn.cursor()
      cursor.execute(
        "SELECT id, name, version, author, description, game_type FROM games"
      )
      rows = cursor.fetchall()
      conn.close()

      games = []
      for r in rows:
        games.append(
          {
            "id": r[0],
            "name": r[1],
            "version": r[2],
            "author": r[3],
            "description": r[4],
            "type": r[5],
          }
        )
      return games

  def list_my_games(self, author_name):
    """列出特定作者的遊戲"""
    with self.lock:
      conn = self._get_conn()
      cursor = conn.cursor()
      cursor.execute(
        "SELECT name, version, game_type FROM games WHERE author = ?", (author_name,)
      )
      rows = cursor.fetchall()
      conn.close()

      games = []
      for r in rows:
        games.append({"name": r[0], "version": r[1], "type": r[2]})
      return games

  def add_review(self, game_name, player_name, rating, comment):
    """P4: 新增或更新評分"""
    with self.lock:
      conn = self._get_conn()
      cursor = conn.cursor()
      try:
        # 使用 REPLACE INTO (若重複則覆蓋) 或 INSERT
        cursor.execute(
          """
                    INSERT INTO reviews (game_name, player_name, rating, comment)
                    VALUES (?, ?, ?, ?)
                    ON CONFLICT(game_name, player_name) 
                    DO UPDATE SET rating=excluded.rating, comment=excluded.comment
                """,
          (game_name, player_name, rating, comment),
        )
        conn.commit()
        return True, "Review submitted"
      except Exception as e:
        return False, str(e)
      finally:
        conn.close()

  def get_game_rating(self, game_name):
    """取得某遊戲的平均分數與評論數 (用於 P1 顯示)"""
    with self.lock:
      conn = self._get_conn()
      cursor = conn.cursor()
      cursor.execute(
        """
              SELECT AVG(rating), COUNT(*) FROM reviews WHERE game_name = ?
          """,
        (game_name,),
      )
      row = cursor.fetchone()
      conn.close()
      if row and row[0]:
        return round(row[0], 1), row[1]  # Avg, Count
      return 0.0, 0
