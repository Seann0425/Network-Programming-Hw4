# Game Store System 

## Overview
這是一個基於 Python Socket 與 PyQt6 實作的線上遊戲商城系統。
系統包含三個主要角色：
1. **Server**: 負責核心邏輯、資料庫、檔案儲存與房間管理。
2. **Developer Client**: 供開發者上架、更新、下架遊戲。
3. **Player Client**: 供玩家瀏覽、下載、評論、並建立房間進行連線對戰。

## Requirements
* Python 3.9+
* uv (Recommended) or pip

## Easy Start (Recommended)

**For Windows:**
Double-click `run.bat`.

**For Linux / macOS:**
Run `./run.sh` in the terminal.

These scripts will automatically:
1. Create a isolated virtual environment (`venv`).
2. Install necessary packages (`PyQt6`).
3. Launch the system menu.