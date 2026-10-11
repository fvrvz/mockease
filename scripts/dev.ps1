<#
.SYNOPSIS
    MockEase Local Development Orchestrator (PowerShell)
.DESCRIPTION
    Starts or stops local development services:
    - PostgreSQL & Redis in Docker Compose
    - FastAPI Backend on host (port 8000)
    - Vue 3 / Vite Frontend on host (port 5173)
.PARAMETER Action
    start, stop, restart, or status (default: start)
.PARAMETER Background
    Run processes in background instead of foreground
#>

[CmdletBinding()]
param (
    [ValidateSet("start", "stop", "restart", "status")]
    [string]$Action = "start",

    [switch]$Background
)

$ErrorActionPreference = "Stop"

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$RootDir = Split-Path -Parent $ScriptDir

$RunDir = Join-Path $RootDir ".run"
$LogDir = Join-Path $RootDir ".logs"
$BackendPidFile = Join-Path $RunDir "backend.pid"
$FrontendPidFile = Join-Path $RunDir "frontend.pid"

if (-not (Test-Path $RunDir)) { New-Item -ItemType Directory -Path $RunDir -Force | Out-Null }
if (-not (Test-Path $LogDir)) { New-Item -ItemType Directory -Path $LogDir -Force | Out-Null }

function Write-Banner {
    Write-Host "============================================================" -ForegroundColor Cyan
    Write-Host "                MockEase Dev Orchestrator (PowerShell)       " -ForegroundColor Cyan
    Write-Host "   DB: Docker (5432, 6379) | Backend: 8000 | UI: 5173       " -ForegroundColor Cyan
    Write-Host "============================================================" -ForegroundColor Cyan
}

function Check-Docker {
    try {
        docker info | Out-Null
    } catch {
        Write-Host "[ERROR] Docker is not running or not installed. Please start Docker Desktop." -ForegroundColor Red
        exit 1
    }
}

function Start-Databases {
    Write-Host "[INFO] Starting PostgreSQL and Redis via Docker Compose..." -ForegroundColor Blue
    Push-Location $RootDir
    try {
        docker compose up -d postgres redis
    } finally {
        Pop-Location
    }

    Write-Host "[INFO] Waiting for PostgreSQL to be healthy..." -ForegroundColor Blue
    $retries = 30
    while ($retries -gt 0) {
        $result = docker compose -f (Join-Path $RootDir "docker-compose.yml") exec -T postgres pg_isready -U mockease -d mockease 2>$null
        if ($LASTEXITCODE -eq 0) { break }
        Start-Sleep -Seconds 1
        $retries--
    }

    if ($retries -eq 0) {
        Write-Host "[ERROR] PostgreSQL failed to become ready in 30 seconds." -ForegroundColor Red
        exit 1
    }
    Write-Host "[OK] PostgreSQL is ready on localhost:5432" -ForegroundColor Green

    Write-Host "[INFO] Waiting for Redis to be healthy..." -ForegroundColor Blue
    $retries = 20
    while ($retries -gt 0) {
        $pong = (docker compose -f (Join-Path $RootDir "docker-compose.yml") exec -T redis redis-cli ping 2>$null).Trim()
        if ($pong -eq "PONG") { break }
        Start-Sleep -Seconds 1
        $retries--
    }
    Write-Host "[OK] Redis is ready on localhost:6379" -ForegroundColor Green
}

function Setup-Backend {
    Write-Host "[INFO] Configuring Backend environment..." -ForegroundColor Blue
    $BackendDir = Join-Path $RootDir "backend"
    $VenvDir = Join-Path $BackendDir ".venv"

    if (-not (Test-Path $VenvDir)) {
        Write-Host "[INFO] Creating virtualenv at backend/.venv..." -ForegroundColor Blue
        python -m venv $VenvDir
    }

    $VenvPython = if ($IsWindows) { Join-Path $VenvDir "Scripts\python.exe" } else { Join-Path $VenvDir "bin/python" }
    $VenvPip = if ($IsWindows) { Join-Path $VenvDir "Scripts\pip.exe" } else { Join-Path $VenvDir "bin/pip" }
    $VenvAlembic = if ($IsWindows) { Join-Path $VenvDir "Scripts\alembic.exe" } else { Join-Path $VenvDir "bin/alembic" }

    # Check if uvicorn installed
    & $VenvPython -c "import uvicorn" 2>$null
    if ($LASTEXITCODE -ne 0) {
        Write-Host "[INFO] Installing backend dependencies..." -ForegroundColor Blue
        & $VenvPip install -r (Join-Path $BackendDir "requirements.txt") -r (Join-Path $BackendDir "requirements-dev.txt")
    }

    Write-Host "[INFO] Running database migrations (Alembic)..." -ForegroundColor Blue
    Push-Location $BackendDir
    try {
        & $VenvAlembic upgrade head
    } finally {
        Pop-Location
    }
    Write-Host "[OK] Backend environment ready and migrations up to date." -ForegroundColor Green
}

function Setup-Frontend {
    Write-Host "[INFO] Configuring Frontend environment..." -ForegroundColor Blue
    $FrontendDir = Join-Path $RootDir "frontend"
    if (-not (Test-Path (Join-Path $FrontendDir "node_modules"))) {
        Write-Host "[INFO] Installing frontend dependencies (npm install)..." -ForegroundColor Blue
        Push-Location $FrontendDir
        try {
            npm install
        } finally {
            Pop-Location
        }
    }
    Write-Host "[OK] Frontend environment ready." -ForegroundColor Green
}

function Start-Services {
    Check-Docker
    Start-Databases
    Setup-Backend
    Setup-Frontend

    $BackendDir = Join-Path $RootDir "backend"
    $FrontendDir = Join-Path $RootDir "frontend"
    $VenvUvicorn = if ($IsWindows) { Join-Path $BackendDir ".venv\Scripts\uvicorn.exe" } else { Join-Path $BackendDir ".venv/bin/uvicorn" }

    if ($Background) {
        Write-Host "[INFO] Starting Backend in background..." -ForegroundColor Blue
        $backendLog = Join-Path $LogDir "backend.log"
        $backendProc = Start-Process -FilePath $VenvUvicorn -ArgumentList "src.main:app", "--reload", "--port", "8000" -WorkingDirectory $BackendDir -RedirectStandardOutput $backendLog -RedirectStandardError $backendLog -PassThru
        $backendProc.Id | Out-File -FilePath $BackendPidFile -Encoding ascii
        Write-Host "[OK] Backend running [PID $($backendProc.Id)] -> http://localhost:8000" -ForegroundColor Green

        Write-Host "[INFO] Starting Frontend in background..." -ForegroundColor Blue
        $frontendLog = Join-Path $LogDir "frontend.log"
        $frontendProc = Start-Process -FilePath "npm" -ArgumentList "run", "dev" -WorkingDirectory $FrontendDir -RedirectStandardOutput $frontendLog -RedirectStandardError $frontendLog -PassThru
        $frontendProc.Id | Out-File -FilePath $FrontendPidFile -Encoding ascii
        Write-Host "[OK] Frontend running [PID $($frontendProc.Id)] -> http://localhost:5173" -ForegroundColor Green

        Write-Host ""
        Write-Host "All development services started in background!" -ForegroundColor Green
        Write-Host "  • Web UI:     http://localhost:5173" -ForegroundColor Green
        Write-Host "  • API Docs:   http://localhost:8000/api/docs" -ForegroundColor Cyan
        Write-Host "  • Stop with:  .\scripts\dev.ps1 -Action stop" -ForegroundColor Yellow
        Write-Host ""
    } else {
        Write-Host "[INFO] Starting Backend and Frontend in separate windows..." -ForegroundColor Blue
        Start-Process -FilePath $VenvUvicorn -ArgumentList "src.main:app", "--reload", "--port", "8000" -WorkingDirectory $BackendDir
        Start-Process -FilePath "npm" -ArgumentList "run", "dev" -WorkingDirectory $FrontendDir

        Write-Host ""
        Write-Host "[OK] Services running:" -ForegroundColor Green
        Write-Host "  • Web UI:   http://localhost:5173" -ForegroundColor Green
        Write-Host "  • API Docs: http://localhost:8000/api/docs" -ForegroundColor Cyan
        Write-Host "  • To stop:  .\scripts\dev.ps1 -Action stop" -ForegroundColor Yellow
        Write-Host ""
    }
}

function Stop-Services {
    Write-Host "[INFO] Stopping development services..." -ForegroundColor Blue

    # Stop recorded backend PID
    if (Test-Path $BackendPidFile) {
        $pidNum = Get-Content $BackendPidFile -ErrorAction SilentlyContinue
        if ($pidNum) {
            try { Stop-Process -Id $pidNum -Force -ErrorAction SilentlyContinue } catch {}
        }
        Remove-Item $BackendPidFile -Force -ErrorAction SilentlyContinue
    }

    # Stop recorded frontend PID
    if (Test-Path $FrontendPidFile) {
        $pidNum = Get-Content $FrontendPidFile -ErrorAction SilentlyContinue
        if ($pidNum) {
            try { Stop-Process -Id $pidNum -Force -ErrorAction SilentlyContinue } catch {}
        }
        Remove-Item $FrontendPidFile -Force -ErrorAction SilentlyContinue
    }

    # Terminate processes listening on port 8000 / 5173 on Windows if available
    try {
        $port8000 = Get-NetTCPConnection -LocalPort 8000 -ErrorAction SilentlyContinue
        if ($port8000) { Stop-Process -Id $port8000.OwningProcess -Force -ErrorAction SilentlyContinue }
    } catch {}

    try {
        $port5173 = Get-NetTCPConnection -LocalPort 5173 -ErrorAction SilentlyContinue
        if ($port5173) { Stop-Process -Id $port5173.OwningProcess -Force -ErrorAction SilentlyContinue }
    } catch {}

    # Stop Docker databases
    Push-Location $RootDir
    try {
        docker compose stop postgres redis 2>$null
    } finally {
        Pop-Location
    }

    Write-Host "[OK] All development services and database containers stopped." -ForegroundColor Green
}

function Get-ServiceStatus {
    Write-Host "MockEase Service Status:" -ForegroundColor Yellow
    Write-Host "----------------------------------------"

    Push-Location $RootDir
    try {
        docker compose ps postgres redis
    } finally {
        Pop-Location
    }

    Write-Host "----------------------------------------"
    # Backend port check
    $backendRunning = $false
    try {
        $conn = Test-NetConnection -ComputerName localhost -Port 8000 -WarningAction SilentlyContinue
        $backendRunning = $conn.TcpTestSucceeded
    } catch {}

    if ($backendRunning) {
        Write-Host "Backend:  RUNNING -> http://localhost:8000" -ForegroundColor Green
    } else {
        Write-Host "Backend:  STOPPED" -ForegroundColor Red
    }

    # Frontend port check
    $frontendRunning = $false
    try {
        $conn = Test-NetConnection -ComputerName localhost -Port 5173 -WarningAction SilentlyContinue
        $frontendRunning = $conn.TcpTestSucceeded
    } catch {}

    if ($frontendRunning) {
        Write-Host "Frontend: RUNNING -> http://localhost:5173" -ForegroundColor Green
    } else {
        Write-Host "Frontend: STOPPED" -ForegroundColor Red
    }
    Write-Host "----------------------------------------"
}

Write-Banner

switch ($Action) {
    "start"   { Start-Services }
    "stop"    { Stop-Services }
    "restart" { Stop-Services; Start-Sleep -Seconds 2; Start-Services }
    "status"  { Get-ServiceStatus }
}
