param(
    [switch]$Restart,
    [int]$ApiPort = 8000,
    [int]$WebPort = 3000,
    [int]$StartupTimeoutSec = 45
)

$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
$WebRoot = Join-Path $Root "apps\web"
$Tmp = Join-Path $Root "tmp"
New-Item -ItemType Directory -Force -Path $Tmp | Out-Null

function Test-PortFree([int]$Port) {
    return -not (Get-NetTCPConnection -LocalPort $Port -State Listen -ErrorAction SilentlyContinue)
}

function Stop-PortListener([int]$Port) {
    # CRG: Restart must work even when Win32_Process/CIM command-line inspection is denied.
    Get-NetTCPConnection -LocalPort $Port -State Listen -ErrorAction SilentlyContinue |
        Select-Object -ExpandProperty OwningProcess -Unique |
        Where-Object { $_ -and $_ -ne $PID } |
        ForEach-Object { Stop-Process -Id $_ -Force -ErrorAction SilentlyContinue }
}

function Wait-HttpStatus([string]$Url, [int]$TimeoutSec) {
    # CRG: Next/FastAPI cold starts often exceed a fixed sleep, so poll until ready or timed out.
    $deadline = (Get-Date).AddSeconds($TimeoutSec)
    do {
        try {
            return (Invoke-WebRequest -Uri $Url -UseBasicParsing -TimeoutSec 5).StatusCode
        } catch {
            Start-Sleep -Seconds 2
        }
    } while ((Get-Date) -lt $deadline)
    return "FAIL"
}

if ($Restart) {
    Stop-PortListener $ApiPort
    Stop-PortListener $WebPort
    Start-Sleep -Seconds 2
}

if (Test-PortFree $ApiPort) {
    $apiOut = Join-Path $Tmp "uvicorn-out.log"
    $apiErr = Join-Path $Tmp "uvicorn-err.log"
    Start-Process -FilePath "python" -ArgumentList "-m","uvicorn","apps.api.main:app","--host","127.0.0.1","--port",$ApiPort -WorkingDirectory $Root -WindowStyle Hidden -RedirectStandardOutput $apiOut -RedirectStandardError $apiErr | Out-Null
}

if (Test-PortFree $WebPort) {
    $nextCmd = Join-Path $WebRoot "node_modules\.bin\next.cmd"
    $webCommand = "set NEXT_PUBLIC_API_BASE_URL=http://127.0.0.1:$ApiPort&& set BACKEND_INTERNAL_URL=http://127.0.0.1:$ApiPort&& `"$nextCmd`" dev --hostname 127.0.0.1 --port $WebPort"
    # CRG: Bypass npm.cmd because this Windows environment can fail in npm's Node entry wrapper.
    Start-Process -FilePath "cmd.exe" -ArgumentList "/c",$webCommand -WorkingDirectory $WebRoot -WindowStyle Hidden | Out-Null
}

$apiHealth = Wait-HttpStatus "http://127.0.0.1:$ApiPort/health" $StartupTimeoutSec
$webHealth = Wait-HttpStatus "http://127.0.0.1:$WebPort/workspace" $StartupTimeoutSec

Write-Output "API  http://127.0.0.1:$ApiPort/health -> $apiHealth"
Write-Output "WEB  http://127.0.0.1:$WebPort/workspace -> $webHealth"
Write-Output "DIAG http://127.0.0.1:$WebPort/settings/integrations"
Write-Output "LOGS $Tmp"
Write-Output "Use .\start-dev.ps1 -Restart if old dev processes are occupying these ports."
