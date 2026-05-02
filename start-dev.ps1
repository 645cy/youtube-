param(
    [switch]$Restart,
    [int]$ApiPort = 8000,
    [int]$WebPort = 3000
)

$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
$WebRoot = Join-Path $Root "apps\web"
$Tmp = Join-Path $Root "tmp"
New-Item -ItemType Directory -Force -Path $Tmp | Out-Null

function Test-PortFree([int]$Port) {
    return -not (Get-NetTCPConnection -LocalPort $Port -State Listen -ErrorAction SilentlyContinue)
}

if ($Restart) {
    # CRG: Stop only project-owned dev processes when the caller explicitly asks for a restart.
    Get-CimInstance Win32_Process |
        Where-Object {
            $_.CommandLine -like "*$Root*" -and
            ($_.CommandLine -like "*uvicorn*" -or $_.CommandLine -like "*next*")
        } |
        ForEach-Object { Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue }
    Start-Sleep -Seconds 2
}

if (Test-PortFree $ApiPort) {
    $apiOut = Join-Path $Tmp "uvicorn-out.log"
    $apiErr = Join-Path $Tmp "uvicorn-err.log"
    Start-Process -FilePath "python" -ArgumentList "-m","uvicorn","apps.api.main:app","--host","127.0.0.1","--port",$ApiPort -WorkingDirectory $Root -WindowStyle Hidden -RedirectStandardOutput $apiOut -RedirectStandardError $apiErr | Out-Null
}

if (Test-PortFree $WebPort) {
    $webCommand = "set NEXT_PUBLIC_API_BASE_URL=http://127.0.0.1:$ApiPort&& npm.cmd run dev -- --hostname 127.0.0.1 --port $WebPort"
    Start-Process -FilePath "cmd.exe" -ArgumentList "/c",$webCommand -WorkingDirectory $WebRoot -WindowStyle Hidden | Out-Null
}

Start-Sleep -Seconds 6

$apiHealth = try { (Invoke-WebRequest -Uri "http://127.0.0.1:$ApiPort/health" -UseBasicParsing -TimeoutSec 8).StatusCode } catch { "FAIL" }
$webHealth = try { (Invoke-WebRequest -Uri "http://127.0.0.1:$WebPort/workspace" -UseBasicParsing -TimeoutSec 8).StatusCode } catch { "FAIL" }

"API  http://127.0.0.1:$ApiPort/health -> $apiHealth"
"WEB  http://127.0.0.1:$WebPort/workspace -> $webHealth"
"DIAG http://127.0.0.1:$WebPort/settings/integrations"
"Use .\start-dev.ps1 -Restart if old dev processes are occupying ports."
