# Deterministic reset: reseed both business databases and clear the audit log.
# Restart signalops-backend afterwards to clear in-memory investigations and the simulated ledger.
$root = Split-Path -Parent $PSScriptRoot
Push-Location (Join-Path $root "nova-orders");    .venv\Scripts\python -m app.seed; Pop-Location
Push-Location (Join-Path $root "nova-inventory"); .venv\Scripts\python -m app.seed; Pop-Location
$audit = Join-Path $root "signalops-backend\audit.jsonl"
if (Test-Path $audit) { Remove-Item $audit -Confirm:$false; Write-Host "audit log cleared" }
if (Test-Path (Join-Path $root "nova-inventory\app\routes\incidents.py")) {
    Write-Warning "nova-inventory/app/routes/incidents.py exists: the live-discovery endpoint is still in place (see docs/live-endpoint.md, Reset)."
}
