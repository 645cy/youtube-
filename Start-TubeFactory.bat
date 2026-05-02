@echo off
setlocal enabledelayedexpansion
chcp 65001 >nul

set "ROOT=%~dp0"
cd /d "%ROOT%"
set "BACKEND_HOST=127.0.0.1"
set "BACKEND_BIND_HOST=0.0.0.0"
set "BACKEND_PORT=8000"
set "FRONTEND_PORT=3000"
set "OPEN_PATH=/dashboard"

echo [TubeFactory] Workspace: %ROOT%

echo [TubeFactory] Cleaning old TubeFactory processes...
powershell -NoProfile -ExecutionPolicy Bypass -Command "$root=[Regex]::Escape((Resolve-Path -LiteralPath $env:ROOT).Path); Get-CimInstance Win32_Process | Where-Object { $_.CommandLine -match $root -and ($_.CommandLine -like '*uvicorn*' -or $_.CommandLine -like '*next*') } | ForEach-Object { Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue }"
powershell -NoProfile -ExecutionPolicy Bypass -Command "$ports=@([int]$env:BACKEND_PORT,[int]$env:FRONTEND_PORT); Get-NetTCPConnection -LocalPort $ports -State Listen -ErrorAction SilentlyContinue | Select-Object -ExpandProperty OwningProcess -Unique | Where-Object { $_ -and $_ -ne $PID } | ForEach-Object { Stop-Process -Id $_ -Force -ErrorAction SilentlyContinue }"
timeout /t 1 /nobreak >nul

if not exist "apps\api\main.py" (
    echo [TubeFactory] ERROR: Backend not found: apps\api\main.py
    pause
    exit /b 1
)

if not exist "apps\web\package.json" (
    echo [TubeFactory] ERROR: Frontend not found: apps\web\package.json
    pause
    exit /b 1
)

if not exist ".env" (
    if exist ".env.example" (
        echo [TubeFactory] .env not found. Creating from .env.example...
        copy ".env.example" ".env" >nul
    )
)

where python >nul 2>nul
if errorlevel 1 (
    echo [TubeFactory] ERROR: python is not available in PATH.
    pause
    exit /b 1
)

where npm >nul 2>nul
if errorlevel 1 (
    echo [TubeFactory] ERROR: npm is not available in PATH.
    pause
    exit /b 1
)

where node >nul 2>nul
if errorlevel 1 (
    echo [TubeFactory] ERROR: node is not available in PATH.
    pause
    exit /b 1
)

if not exist "apps\web\node_modules" (
    echo [TubeFactory] Installing frontend dependencies...
    pushd "apps\web"
    call npm install
    if errorlevel 1 (
        popd
        echo [TubeFactory] ERROR: npm install failed.
        pause
        exit /b 1
    )
    popd
)

powershell -NoProfile -ExecutionPolicy Bypass -Command "if (Get-NetTCPConnection -LocalPort ([int]$env:BACKEND_PORT) -State Listen -ErrorAction SilentlyContinue) { exit 0 } else { exit 1 }"
if not errorlevel 1 (
    echo [TubeFactory] WARN: Port %BACKEND_PORT% is already in use. Backend may already be running.
) else (
    echo [TubeFactory] Starting backend on port %BACKEND_PORT%...
    start "TubeFactory-Backend" cmd /k "cd /d ""%ROOT%"" && python -m uvicorn apps.api.main:app --host %BACKEND_BIND_HOST% --port %BACKEND_PORT%"
)

timeout /t 4 /nobreak >nul

powershell -NoProfile -ExecutionPolicy Bypass -Command "try { $uri='http://' + $env:BACKEND_HOST + ':' + $env:BACKEND_PORT + '/health'; $r = Invoke-WebRequest -UseBasicParsing -Uri $uri -TimeoutSec 8; if ($r.StatusCode -ge 200 -and $r.StatusCode -lt 300) { exit 0 } else { exit 1 } } catch { exit 1 }"
if errorlevel 1 (
    echo [TubeFactory] ERROR: Backend health check failed: http://%BACKEND_HOST%:%BACKEND_PORT%/health
    echo [TubeFactory] Check the TubeFactory-Backend window for details.
    pause
    exit /b 1
)

if not exist "apps\web\.next" (
    echo [TubeFactory] Building frontend...
    pushd "apps\web"
    call npm run build
    if errorlevel 1 (
        popd
        echo [TubeFactory] ERROR: frontend build failed.
        pause
        exit /b 1
    )
    popd
)

set "NEXT_PUBLIC_API_BASE_URL=http://%BACKEND_HOST%:%BACKEND_PORT%"

powershell -NoProfile -ExecutionPolicy Bypass -Command "if (Get-NetTCPConnection -LocalPort ([int]$env:FRONTEND_PORT) -State Listen -ErrorAction SilentlyContinue) { exit 0 } else { exit 1 }"
if not errorlevel 1 (
    echo [TubeFactory] WARN: Port %FRONTEND_PORT% is already in use. Frontend may already be running.
) else (
    echo [TubeFactory] Starting frontend on port %FRONTEND_PORT%...
    start "TubeFactory-Frontend" cmd /k "cd /d ""%ROOT%apps\web"" && set ""NEXT_PUBLIC_API_BASE_URL=http://%BACKEND_HOST%:%BACKEND_PORT%"" && npm run start -- -p %FRONTEND_PORT%"
)

timeout /t 4 /nobreak >nul

echo [TubeFactory] Opening browser...
start http://127.0.0.1:%FRONTEND_PORT%%OPEN_PATH%

echo.
echo ==========================================
echo TubeFactory is running
echo Backend:  http://%BACKEND_HOST%:%BACKEND_PORT%
echo Frontend: http://127.0.0.1:%FRONTEND_PORT%%OPEN_PATH%
echo Docs:     http://%BACKEND_HOST%:%BACKEND_PORT%/docs
echo Health:   http://%BACKEND_HOST%:%BACKEND_PORT%/health
echo ==========================================
pause
