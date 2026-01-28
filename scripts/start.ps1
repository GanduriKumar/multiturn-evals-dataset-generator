$ErrorActionPreference = "Stop"

$repoRoot = Split-Path -Parent $PSScriptRoot
$backendPidPath = Join-Path $PSScriptRoot ".backend.pid"
$frontendPidPath = Join-Path $PSScriptRoot ".frontend.pid"

$pythonExe = Join-Path $repoRoot ".venv\Scripts\python.exe"
$backendArgs = "-m uvicorn backend.app.main:app --reload --host 127.0.0.1 --port 8000"

$backendCommand = "Set-Location '$repoRoot'; $pythonExe $backendArgs"
$backendProcess = Start-Process -FilePath "powershell.exe" -ArgumentList "-NoExit", "-Command", $backendCommand -WorkingDirectory $repoRoot -PassThru
$backendProcess.Id | Set-Content -Path $backendPidPath

$frontendDir = Join-Path $repoRoot "frontend"
$frontendCommand = "Set-Location '$frontendDir'; if (-not (Test-Path 'node_modules')) { npm install }; npm run dev"
$frontendProcess = Start-Process -FilePath "powershell.exe" -ArgumentList "-NoExit", "-Command", $frontendCommand -WorkingDirectory $frontendDir -PassThru
$frontendProcess.Id | Set-Content -Path $frontendPidPath

Write-Host "Backend PID: $($backendProcess.Id)"
Write-Host "Frontend PID: $($frontendProcess.Id)"
Write-Host "Backend: http://localhost:8000"
Write-Host "Frontend: http://localhost:5173"
