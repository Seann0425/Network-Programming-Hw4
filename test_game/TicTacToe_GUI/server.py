import socket
import argparse
import sys
import threading
import time


class TicTacToeServer:
  def __init__(self, port, room_id):
    self.port = port
    self.room_id = room_id
    self.host = "0.0.0.0"
    self.server_socket = None
    self.players = []  # [Player1(X), Player2(O)]
    self.board = [" " for _ in range(9)]
    self.current_turn = 0  # 0=X, 1=O
    self.game_over = False

  def start(self):
    try:
      self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
      self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
      self.server_socket.bind((self.host, self.port))
      self.server_socket.listen(2)

      print(f"[GameServer] Listening on {self.host}:{self.port}", flush=True)

      self.accept_players()
      self.game_loop()

    except Exception as e:
      print(f"[Fatal Error] Server crashed: {e}", flush=True)
    finally:
      self.close_server()

  def accept_players(self):
    print("Waiting for players...", flush=True)
    while len(self.players) < 2:
      client_sock, addr = self.server_socket.accept()
      player_id = len(self.players) + 1
      print(f"Player {player_id} connected from {addr}", flush=True)
      self.players.append(client_sock)

      # 通知玩家身分
      symbol = "X" if player_id == 1 else "O"
      self.send_msg(
        client_sock, f"INFO:Welcome Player {player_id}. You are '{symbol}'."
      )
      if player_id == 1:
        self.send_msg(client_sock, "INFO:Waiting for opponent...")

    print("Both players connected. Game starting!", flush=True)
    # 廣播初始空盤面
    self.broadcast_board()
    self.broadcast("INFO:Game Start!")

  def game_loop(self):
    while not self.game_over:
      current_player_idx = self.current_turn % 2
      opponent_idx = (self.current_turn + 1) % 2

      player_sock = self.players[current_player_idx]
      opponent_sock = self.players[opponent_idx]
      symbol = "X" if current_player_idx == 0 else "O"

      # 1. 更新雙方盤面
      self.broadcast_board()

      # 2. 通知等待方
      self.send_msg(opponent_sock, f"INFO:Waiting for {symbol} to move...")

      # 3. 通知當前玩家下棋 (發送 INPUT_REQ)
      self.send_msg(player_sock, f"INFO:Your turn ({symbol}).\nINPUT_REQ")

      # 4. 接收移動
      while True:
        try:
          move_str = self.recv_msg(player_sock)
          if not move_str:
            print(f"Player {current_player_idx + 1} disconnected.", flush=True)
            self.game_over = True
            return

          if move_str.isdigit():
            pos = int(move_str)
            if 0 <= pos <= 8 and self.board[pos] == " ":
              self.board[pos] = symbol
              break
            else:
              # 非法移動，雖然後端擋住，但 GUI 應該也會擋
              self.send_msg(player_sock, "INFO:Invalid move.")
          else:
            self.send_msg(player_sock, "INFO:Invalid input.")
        except Exception as e:
          print(f"Error receiving move: {e}", flush=True)
          self.game_over = True
          return

      # 5. 檢查勝負
      winner = self.check_winner()
      if winner:
        self.broadcast_board()  # 更新最後一手
        if winner == "Draw":
          self.broadcast("GAME_OVER:Draw")
        else:
          self.broadcast(f"GAME_OVER:Player {symbol} wins!")
        self.game_over = True
      else:
        self.current_turn += 1

    # 遊戲結束後停留 2 秒確保訊息送達，然後關閉
    time.sleep(2)

  def broadcast_board(self):
    # 格式: BOARD_DATA:X, ,O, ,X,...
    raw_board = ",".join(self.board)
    self.broadcast(f"BOARD_DATA:{raw_board}")

  def check_winner(self):
    win_conditions = [
      (0, 1, 2),
      (3, 4, 5),
      (6, 7, 8),
      (0, 3, 6),
      (1, 4, 7),
      (2, 5, 8),
      (0, 4, 8),
      (2, 4, 6),
    ]
    for x, y, z in win_conditions:
      if self.board[x] == self.board[y] == self.board[z] and self.board[x] != " ":
        return self.board[x]
    if " " not in self.board:
      return "Draw"
    return None

  def send_msg(self, sock, msg):
    try:
      sock.sendall(msg.encode("utf-8"))
    except:
      pass

  def recv_msg(self, sock):
    try:
      return sock.recv(1024).decode("utf-8").strip()
    except:
      return None

  def broadcast(self, msg):
    for p in self.players:
      self.send_msg(p, msg)

  def close_server(self):
    print("Shutting down game server...", flush=True)
    for p in self.players:
      try:
        p.close()
      except:
        pass
    if self.server_socket:
      self.server_socket.close()


if __name__ == "__main__":
  parser = argparse.ArgumentParser()
  parser.add_argument("--port", type=int, required=True)
  parser.add_argument("--room_id", type=str, required=True)
  args = parser.parse_args()

  server = TicTacToeServer(args.port, args.room_id)
  server.start()
