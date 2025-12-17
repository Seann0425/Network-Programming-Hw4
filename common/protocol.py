# GameStore/common/protocol.py

import socket
import struct
import json
import os
from .constants import Command

# Header format:
#   Payload Length (4 bytes, unsigned int, big-endian)
#   Command Code   (4 bytes, unsigned int, big-endian)
HEADER_STRUCT = struct.Struct("!II")


def send_request(sock: socket.socket, cmd: Command, data: dict = None):
  """
  將指令與資料封裝成封包並發送。
  格式: [Length (4B)][Cmd (4B)][JSON Payload]
  """
  if data is None:
    data = {}

  # 1. 序列化 JSON Payload
  json_bytes = json.dumps(data).encode("utf-8")

  # 2. 計算長度與準備 Header
  payload_len = len(json_bytes)
  cmd_value = cmd.value

  # 3. 打包 Header
  header = HEADER_STRUCT.pack(payload_len, cmd_value)

  # 4. 發送 (Header + Body)
  sock.sendall(header + json_bytes)


def recv_request(sock: socket.socket):
  """
  從 Socket 接收完整封包並解析。
  回傳: (Command, dict_data)
  """
  try:
    # 1. 先讀取 Header (固定 8 bytes)
    header_data = _recvall(sock, HEADER_STRUCT.size)
    if not header_data:
      return None, None  # 連線關閉

    payload_len, cmd_value = HEADER_STRUCT.unpack(header_data)

    # 2. 再根據長度讀取 Body
    if payload_len > 0:
      payload_data = _recvall(sock, payload_len)
      if not payload_data:
        raise ConnectionError("Incomplete payload received")

      # 解析 JSON
      data = json.loads(payload_data.decode("utf-8"))
    else:
      data = {}

    try:
      cmd = Command(cmd_value)
    except ValueError:
      # 收到未知的 Command，可能需要處理或忽略
      print(f"[Protocol] Unknown command received: {cmd_value}")
      cmd = Command.ERROR

    return cmd, data

  except ConnectionResetError:
    return None, None
  except Exception as e:
    print(f"[Protocol] Error: {e}")
    return None, None


def _recvall(sock: socket.socket, n: int) -> bytes:
  """
  輔助函式：確保從 socket 精確讀取 n 個 bytes。
  解決 TCP 分包問題。
  """
  data = b""
  while len(data) < n:
    try:
      packet = sock.recv(n - len(data))
      if not packet:
        return None
      data += packet
    except OSError:
      return None
  return data


def send_file(sock: socket.socket, file_path: str):
  """
  發送檔案內容 (Raw Bytes)。
  注意：發送前應先透過 send_request 告知 Server 檔案大小。
  """
  if not os.path.exists(file_path):
    raise FileNotFoundError(f"File not found: {file_path}")

  file_size = os.path.getsize(file_path)

  # 使用 sendfile (Zero-copy optimization if available) 或 chunk read
  with open(file_path, "rb") as f:
    # 這裡為了跨平台相容性，使用標準 chunk 傳輸
    while True:
      chunk = f.read(4096)
      if not chunk:
        break
      sock.sendall(chunk)


def recv_file(
  sock: socket.socket, file_size: int, save_path: str, progress_callback=None
):
  """
  接收指定大小的檔案並寫入 save_path。
  """
  received = 0
  with open(save_path, "wb") as f:
    while received < file_size:
      # 計算剩餘大小，避免多讀到下一個封包的 Header
      bytes_to_read = min(4096, file_size - received)
      chunk = sock.recv(bytes_to_read)
      if not chunk:
        raise ConnectionError("Connection lost while receiving file")

      f.write(chunk)
      received += len(chunk)

      if progress_callback:
        progress_callback(received, file_size)
