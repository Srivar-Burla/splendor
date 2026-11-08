@echo off
cd /d "%~dp0"
echo Starting Splendor...
start "" powershell -NoProfile -WindowStyle Hidden -Command "Start-Sleep -Seconds 2; Start-Process 'http://127.0.0.1:8000'"
where python >nul 2>nul
if %errorlevel%==0 (
  python server.py
) else (
  py -3 server.py
)
pause
