@echo off
title Video Manager - One-Click Startup
echo ============================================
echo    Video Manager System - Quick Start
echo ============================================
echo.
echo This will start both backend and frontend servers
echo Backend: http://127.0.0.1:5000
echo Frontend: http://localhost:5173
echo.
echo Press any key to continue or Ctrl+C to cancel...
pause > nul

echo.
echo Starting backend server in new window...
start "Video Manager Backend" /D "%~dp0" start_backend.bat

echo Waiting 5 seconds for backend to initialize...
timeout /t 5 /nobreak > nul

echo.
echo Starting frontend server in new window...
start "Video Manager Frontend" /D "%~dp0" start_frontend.bat

echo.
echo ============================================
echo    Both servers are starting up!
echo ============================================
echo.
echo Backend Server: http://127.0.0.1:5000
echo Frontend App:   http://localhost:5173
echo.
echo Wait for both servers to fully load, then open:
echo http://localhost:5173 in your web browser
echo.
echo Press any key to exit this launcher...
pause > nul