@echo off
echo Starting Video Manager Frontend Development Server...
echo.

cd /d "%~dp0frontend"

echo Checking Node.js dependencies...
if not exist node_modules (
    echo Installing frontend dependencies...
    npm install
)

echo Starting Vite development server...
echo Frontend will be available at: http://localhost:5173
echo.
npm run dev

pause