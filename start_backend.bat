@echo off
echo Starting Video Manager Backend Server...
echo.

cd /d "%~dp0backend"

if not exist venv (
    echo Creating virtual environment...
    python -m venv venv
)

echo Activating virtual environment...
call venv\Scripts\activate

echo Installing dependencies...
pip install -r requirements.txt

echo Starting Flask backend server...
echo Backend will be available at: http://127.0.0.1:5000
echo.
python app.py

pause