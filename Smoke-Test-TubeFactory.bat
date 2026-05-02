@echo off
setlocal enabledelayedexpansion
chcp 65001 >nul

set "ROOT=%~dp0"
cd /d "%ROOT%"

if not defined API_BASE set "API_BASE=http://127.0.0.1:8000"
if not defined WEB_BASE set "WEB_BASE=http://127.0.0.1:3000"
if not defined API_PREFIX set "API_PREFIX=/api/v1"
set "FAILURES=0"

echo [Smoke] TubeFactory smoke test started.
echo [Smoke] Workspace: %ROOT%
echo.

where curl.exe >nul 2>nul
if errorlevel 1 (
    echo [Smoke] ERROR: curl.exe is not available.
    exit /b 1
)

call :CHECK_URL "Backend health" "%API_BASE%/health" "status"
call :CHECK_URL "Channels list" "%API_BASE%%API_PREFIX%/channels" "items"
call :CHECK_URL "Channel tags" "%API_BASE%%API_PREFIX%/channels/tags" "["
call :CHECK_URL "Dashboard KPI" "%API_BASE%%API_PREFIX%/analysis/dashboard" "total_channels"
call :CHECK_URL "Lab paths" "%API_BASE%%API_PREFIX%/lab/paths" "path_id"
call :CHECK_URL "Radar monitors" "%API_BASE%%API_PREFIX%/radar/monitors" "["
call :CHECK_URL "Topic discovery" "%API_BASE%%API_PREFIX%/content-factory/topic-discovery?niche=tech" "topic_suggestions"
call :CHECK_URL "Crawler tasks" "%API_BASE%%API_PREFIX%/crawler/tasks" "["

call :CHECK_POST_URL "Title optimization" "%API_BASE%%API_PREFIX%/content-factory/title-optimization?title=How%%20to%%20Make%%20Money%%20with%%20AI&target_audience=tech" "improved_title_suggestions"
call :CHECK_POST_URL "Shot list" "%API_BASE%%API_PREFIX%/content-factory/shot-list?video_duration_minutes=6&camera_count=1&has_b_roll=true" "shot_list"

call :CHECK_URL "Frontend dashboard" "%WEB_BASE%/dashboard" "/dashboard"
call :CHECK_URL "Frontend radar" "%WEB_BASE%/radar" "/radar"
call :CHECK_URL "Frontend crawler" "%WEB_BASE%/crawler" "/crawler"
call :CHECK_URL "Frontend lab" "%WEB_BASE%/lab" "/lab"
call :CHECK_URL "Frontend factory" "%WEB_BASE%/factory" "/factory"

echo.
if "%FAILURES%"=="0" (
    echo [Smoke] All checks passed.
    exit /b 0
)

echo [Smoke] FAILED checks: %FAILURES%
exit /b 1

:CHECK_URL
set "NAME=%~1"
set "URL=%~2"
set "EXPECTED=%~3"
set "TMP=%TEMP%\tubefactory-smoke-%RANDOM%.txt"
curl.exe --silent --show-error --max-time 10 "%URL%" > "%TMP%"
if errorlevel 1 (
    echo [Smoke] FAIL: %NAME% - request failed
    set /a FAILURES+=1
    del "%TMP%" >nul 2>nul
    exit /b 0
)
findstr /C:"%EXPECTED%" "%TMP%" >nul
if errorlevel 1 (
    echo [Smoke] FAIL: %NAME% - expected "%EXPECTED%"
    set /a FAILURES+=1
) else (
    echo [Smoke] PASS: %NAME%
)
del "%TMP%" >nul 2>nul
exit /b 0

:CHECK_POST_URL
set "NAME=%~1"
set "URL=%~2"
set "EXPECTED=%~3"
set "TMP=%TEMP%\tubefactory-smoke-%RANDOM%.txt"
curl.exe --silent --show-error --max-time 10 -X POST "%URL%" > "%TMP%"
if errorlevel 1 (
    echo [Smoke] FAIL: %NAME% - request failed
    set /a FAILURES+=1
    del "%TMP%" >nul 2>nul
    exit /b 0
)
findstr /C:"%EXPECTED%" "%TMP%" >nul
if errorlevel 1 (
    echo [Smoke] FAIL: %NAME% - expected "%EXPECTED%"
    set /a FAILURES+=1
) else (
    echo [Smoke] PASS: %NAME%
)
del "%TMP%" >nul 2>nul
exit /b 0
