#!/bin/bash

# 定義虛擬環境資料夾名稱
VENV_DIR="venv"

# 1. 檢查是否已有 venv，沒有就建立
if [ ! -d "$VENV_DIR" ]; then
    echo "[Script] Creating virtual environment..."
    python3 -m venv $VENV_DIR
fi

# 2. 啟動虛擬環境
echo "[Script] Activating virtual environment..."
source $VENV_DIR/bin/activate

# 3. 安裝依賴 (如果 requirements.txt 存在)
if [ -f "requirements.txt" ]; then
    echo "[Script] Checking dependencies..."
    pip install -r requirements.txt > /dev/null
fi

# 4. 執行啟動腳本 (這裡改成你實際的啟動腳本名稱，例如 launcher.py 或 start_client.py)
echo "[Script] Starting Launcher..."
python3 start_client.py