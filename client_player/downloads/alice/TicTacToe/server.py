import socket
import argparse
import sys
import threading


class TicTacToeServer:
  def __init__(self, port, room_id):
    self.port = port
    self.room_id = room_id
    self.host = "0.0.0.0"
    self.server_socket = None
    self.players = []  # 存放 [socket, socket]
    self.board = [" " for _ in range(9)]
    self.current_turn = 0  # 0 for Player 1 (X), 1 for Player 2 (O)
    self.game_over = False

  def start(self):
    """啟動 Server 並等待玩家連線"""
    try:
      self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
      # 允許 Port 重用，避免 server 重啟時卡在 TIME_WAIT
      self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
      self.server_socket.bind((self.host, self.port))
      self.server_socket.listen(2)

      print(f"[Game Server {self.room_id}] Listening on {self.host}:{self.port}")

      # 等待兩位玩家
      self.accept_players()

      # 開始遊戲主迴圈
      self.game_loop()

    except Exception as e:
      print(f"[Error] Server crashed: {e}")
    finally:
      self.close_server()

  def accept_players(self):
    """等待兩位玩家連線"""
    print("Waiting for players...")
    while len(self.players) < 2:
      client_sock, addr = self.server_socket.accept()
      player_id = len(self.players) + 1
      print(f"Player {player_id} connected from {addr}")

      self.players.append(client_sock)

      # 簡單通知玩家身分
      msg = f"Welcome! You are Player {player_id} ({'X' if player_id == 1 else 'O'})."
      if player_id == 1:
        msg += " Waiting for opponent..."
      self.send_msg(client_sock, msg)

    print("Both players connected. Game starting!")
    self.broadcast("Game Start!")

  def game_loop(self):
    """遊戲核心邏輯"""
    while not self.game_over:
      current_player_idx = self.current_turn % 2
      opponent_idx = (self.current_turn + 1) % 2

      player_sock = self.players[current_player_idx]
      opponent_sock = self.players[opponent_idx]

      symbol = "X" if current_player_idx == 0 else "O"

      # 1. 發送盤面給雙方
      board_str = self.format_board()
      self.broadcast(f"\n{board_str}\n")

      # 2. 通知等待方
      self.send_msg(opponent_sock, "Waiting for opponent's move...")

      # 3. 要求當前玩家下棋
      while True:
        self.send_msg(
          player_sock, f"Your turn ({symbol}). Enter position (0-8): INPUT_REQ"
        )

        try:
          move_str = self.recv_msg(player_sock)
          if not move_str:  # Client 斷線
            print(f"Player {current_player_idx + 1} disconnected.")
            self.game_over = True
            return

          if move_str.isdigit():
            pos = int(move_str)
            if 0 <= pos <= 8 and self.board[pos] == " ":
              self.board[pos] = symbol
              break
            else:
              self.send_msg(player_sock, "Invalid move. Try again.")
          else:
            self.send_msg(player_sock, "Invalid input. Please enter a number 0-8.")
        except Exception as e:
          print(f"Error receiving move: {e}")
          self.game_over = True
          return

      # 4. 檢查勝負
      winner = self.check_winner()
      if winner:
        final_board = self.format_board()
        self.broadcast(f"\n{final_board}\n")
        if winner == "Draw":
          self.broadcast("Game Over! It's a Draw!")
        else:
          self.broadcast(f"Game Over! Player {current_player_idx + 1} ({winner}) wins!")
        self.game_over = True
      else:
        self.current_turn += 1

  def format_board(self):
    """將盤面格式化為字串"""
    b = self.board
    return (
      f" {b[0]} | {b[1]} | {b[2]} \n"
      f"---+---+---\n"
      f" {b[3]} | {b[4]} | {b[5]} \n"
      f"---+---+---\n"
      f" {b[6]} | {b[7]} | {b[8]} "
    )

  def check_winner(self):
    """檢查是否有贏家"""
    win_conditions = [
      (0, 1, 2),
      (3, 4, 5),
      (6, 7, 8),  # Rows
      (0, 3, 6),
      (1, 4, 7),
      (2, 5, 8),  # Cols
      (0, 4, 8),
      (2, 4, 6),  # Diagonals
    ]

    for x, y, z in win_conditions:
      if self.board[x] == self.board[y] == self.board[z] and self.board[x] != " ":
        return self.board[x]

    if " " not in self.board:
      return "Draw"

    return None

  def send_msg(self, sock, msg):
    """簡單的 Protocol: 傳送 UTF-8 字串"""
    try:
      sock.sendall(msg.encode("utf-8"))
    except Exception as e:
      print(f"Send error: {e}")

  def recv_msg(self, sock):
    """簡單的 Protocol: 接收 UTF-8 字串 (Buffer size 1024)"""
    try:
      data = sock.recv(1024)
      return data.decode("utf-8").strip()
    except Exception as e:
      print(f"Recv error: {e}")
      return None

  def broadcast(self, msg):
    """廣播訊息給所有玩家"""
    for p in self.players:
      self.send_msg(p, msg)

  def close_server(self):
    """關閉資源"""
    print("Shutting down game server...")
    for p in self.players:
      try:
        p.close()
      except:
        pass
    if self.server_socket:
      self.server_socket.close()


if __name__ == "__main__":
  parser = argparse.ArgumentParser(description="Tic-Tac-Toe Game Server")
  parser.add_argument("--port", type=int, required=True, help="Port to listen on")
  parser.add_argument(
    "--room_id", type=str, required=True, help="Room ID for identification"
  )

  args = parser.parse_args()

  server = TicTacToeServer(args.port, args.room_id)
  server.start()
