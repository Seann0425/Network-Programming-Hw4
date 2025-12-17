@echo off
set VENV_DIR=venv

REM 1. 檢查是否已有 venv，沒有就建立
if not exist %VENV_DIR% (
    echo [Script] Creating virtual environment...
    python -m venv %VENV_DIR%
)

REM 2. 啟動虛擬環境
call %VENV_DIR%\Scripts\activate

REM 3. 安裝依賴
if exist requirements.txt (
    echo [Script] Installing dependencies...
    pip install -r requirements.txt
)

REM 4. 執行啟動腳本
echo [Script] Starting Launcher...
python start_client.py

REM 結束後停留在視窗讓助教看 Log (可選)
pause