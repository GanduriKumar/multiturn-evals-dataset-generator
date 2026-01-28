$ErrorActionPreference = "Stop"

$backendPidPath = Join-Path $PSScriptRoot ".backend.pid"
$frontendPidPath = Join-Path $PSScriptRoot ".frontend.pid"

$pidFiles = @($backendPidPath, $frontendPidPath)
foreach ($pidFile in $pidFiles) {
    if (-not (Test-Path $pidFile)) {
        continue
    }

    $pidText = (Get-Content -Path $pidFile | Select-Object -First 1)
    $processId = 0
    $isValidPid = [int]::TryParse($pidText, [ref]$processId)

    if ($isValidPid -and $processId -gt 0) {
        $allPids = New-Object System.Collections.Generic.HashSet[int]
        $queue = New-Object System.Collections.Generic.Queue[int]
        $queue.Enqueue($processId)

        while ($queue.Count -gt 0) {
            $current = $queue.Dequeue()
            if (-not $allPids.Add($current)) {
                continue
            }

            $children = Get-CimInstance Win32_Process -Filter "ParentProcessId=$current" -ErrorAction SilentlyContinue
            foreach ($child in $children) {
                if ($child.ProcessId -gt 0) {
                    $queue.Enqueue([int]$child.ProcessId)
                }
            }
        }

        foreach ($targetPid in $allPids) {
            $process = Get-Process -Id $targetPid -ErrorAction SilentlyContinue
            if ($process) {
                Stop-Process -Id $targetPid -Force -ErrorAction SilentlyContinue
            }
        }
    }

    Remove-Item -Path $pidFile -Force
}

Write-Host "Stopped backend and frontend if running."
