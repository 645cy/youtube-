@echo off
chcp 65001 >nul
echo [TubeFactory] Stopping TubeFactory service windows...

taskkill /F /FI "WINDOWTITLE eq TubeFactory-Backend*" >nul 2>nul
taskkill /F /FI "WINDOWTITLE eq TubeFactory-Frontend*" >nul 2>nul

echo [TubeFactory] Checking ports 8000 and 3000...
for /f "tokens=5" %%a in ('netstat -ano ^| findstr ":8000"') do taskkill /F /PID %%a >nul 2>nul
for /f "tokens=5" %%a in ('netstat -ano ^| findstr ":3000"') do taskkill /F /PID %%a >nul 2>nul

echo [TubeFactory] Stop command completed.
pause
