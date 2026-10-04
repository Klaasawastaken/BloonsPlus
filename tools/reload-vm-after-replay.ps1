$ErrorActionPreference = 'Stop'
$uri = 'http://127.0.0.1:4173'
$deadline = (Get-Date).AddHours(1)
$logFile = Join-Path $env:LOCALAPPDATA 'BloonsPlus\replay-update.log'
New-Item -ItemType Directory -Force (Split-Path $logFile) | Out-Null
function Note([string]$message) { Add-Content -LiteralPath $logFile -Value ('{0:o} {1}' -f (Get-Date), $message) }
Note 'Waiting for the active replay to finish before loading repaired engine files.'
while ((Get-Date) -lt $deadline) {
    try {
        $status = Invoke-RestMethod "$uri/api/farm/status" -TimeoutSec 5
        if (-not $status.running) { break }
    } catch { Note ('Status unavailable: ' + $_.Exception.Message) }
    Start-Sleep -Seconds 5
}
if ((Get-Date) -ge $deadline) { Note 'Timed out; active replay was not interrupted.'; exit 1 }
try {
    # Older VM installs can leave a standalone Node server running on port 4173.
    # Restarting Electron alone then reconnects to that stale server, so repaired
    # route-selection code never loads. Stop only this install's server process.
    $appRoot = Join-Path $env:LOCALAPPDATA 'Programs\Bloons+\resources\app'
    $nodeExe = Join-Path $appRoot 'node.exe'
    Get-CimInstance Win32_Process -Filter "Name='node.exe'" -ErrorAction SilentlyContinue |
        Where-Object { $_.ExecutablePath -ieq $nodeExe -and $_.CommandLine -match 'server[.]js' } |
        ForEach-Object { Stop-Process -Id $_.ProcessId -ErrorAction Stop; Note ('Stopped stale Bloons+ server PID ' + $_.ProcessId) }
    # Close only the Bloons+ UI. BTD6 stays open on its current screen.
    Get-Process -Name 'Bloons+' -ErrorAction SilentlyContinue | Stop-Process
    Start-Sleep -Seconds 2
    & schtasks /run /tn BloonsPlusApp | Out-Null
    if ($LASTEXITCODE -ne 0) { throw 'Could not restart the BloonsPlusApp task' }
    $readyDeadline = (Get-Date).AddMinutes(2)
    while ((Get-Date) -lt $readyDeadline) {
        Start-Sleep -Seconds 3
        try {
            $ready = Invoke-RestMethod "$uri/api/farm/status" -TimeoutSec 5
            if ($ready.running) { Note 'Sweep already resumed.'; exit 0 }
            $result = Invoke-RestMethod "$uri/api/farm/start" -Method Post -ContentType 'application/json' -Body '{"type":"black-border-sweep"}' -TimeoutSec 60
            if ($result.ok) { Note 'Repaired controller loaded; sweep resumed.'; exit 0 }
        } catch { Note ('Waiting for controller: ' + $_.Exception.Message) }
    }
    throw 'Controller did not become ready within two minutes'
} catch { Note ('Update failed: ' + $_.Exception.Message); exit 1 }
