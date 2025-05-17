
@echo off
cd backend
if not exist venv (
    echo 建立虛擬環境...
    python -m venv venv
)
echo 啟動虛擬環境...
call venv\Scripts\activate
echo 安裝 Flask 與 CORS...
pip install -r requirements.txt
echo 啟動 Flask 伺服器...
python app.py
pause
