@echo off
set VENV_DIR=.venv

REM 1. 檢查並建立虛擬環境
if not exist %VENV_DIR% (
    echo [Script] Creating virtual environment...
    python -m venv %VENV_DIR%
)

REM 2. 啟動虛擬環境 (這步很重要，後面的 pip 才會裝在 venv 裡)
call %VENV_DIR%\Scripts\activate

REM 3. 安裝依賴
if exist requirements.txt (
    echo [Script] Checking dependencies...

    REM 升級 pip (避免舊版 pip 報錯)
    python -m pip install --upgrade pip

    REM 安裝 requirements.txt (請確保裡面只寫了 PyQt6)
    pip install -r requirements.txt
)

REM 4. [關鍵修正] 執行 demo.py (不是 start_client.py)
echo [Script] Starting Launcher...
if exist demo.py (
    python demo.py
) else (
    echo [Error] demo.py not found! Please make sure the file exists.
    pause
)

REM 結束前暫停，方便查看錯誤
pause