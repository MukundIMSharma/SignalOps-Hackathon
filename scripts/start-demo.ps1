# Starts all four SignalOps processes, each in its own window. Usage: powershell -File scripts\start-demo.ps1 [-Reset]
param([switch]$Reset)
$root = Split-Path -Parent $PSScriptRoot
if ($Reset) { & "$PSScriptRoot\reset-demo.ps1" }

function Start-Window($title, $dir, $cmd) {
    Start-Process powershell -WorkingDirectory (Join-Path $root $dir) -ArgumentList "-NoExit", "-Command", "`$host.UI.RawUI.WindowTitle='$title'; $cmd"
}
Start-Window "nova-orders :8001"    "nova-orders"        ".venv\Scripts\python -m uvicorn app.main:app --port 8001"
Start-Window "nova-inventory :8002" "nova-inventory"     ".venv\Scripts\python -m uvicorn app.main:app --port 8002"
Start-Sleep -Seconds 3
Start-Window "signalops-backend :8000" "signalops-backend" ".venv\Scripts\python -m uvicorn main:app --port 8000"
Start-Window "signalops-frontend :5173" "signalops-frontend" "npm run dev"

# wait until every service answers
# uvicorn binds IPv4 only; PS 5.1 tries ::1 first for "localhost"
foreach ($u in "http://127.0.0.1:8001/health", "http://127.0.0.1:8002/health", "http://127.0.0.1:8000/api/health", "http://localhost:5173/") {
    $ok = $false
    for ($i = 0; $i -lt 30 -and -not $ok; $i++) {
        try { Invoke-WebRequest $u -UseBasicParsing -TimeoutSec 2 | Out-Null; $ok = $true } catch { Start-Sleep -Seconds 1 }
    }
    Write-Host ("{0,-36} {1}" -f $u, $(if ($ok) { "up" } else { "NOT RESPONDING" }))
}
Write-Host "Open http://localhost:5173"
