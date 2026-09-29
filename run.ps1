[CmdletBinding()]
param(
    [Parameter(Position=0)]
    [int]$Port = 8501,
    [Parameter(Position=1)]
    [int]$ApiPort = 8000
)

# 1. Guarantee working directory is the script root from anywhere
Set-Location -LiteralPath $PSScriptRoot

$env:FASLYN_API_PORT = "$ApiPort"

Write-Host "===================================================" -ForegroundColor Green
Write-Host "  Faslyn - BRICS AgriN Intelligence Platform" -ForegroundColor Green
Write-Host "===================================================" -ForegroundColor Green
Write-Host ""
Write-Host "[1/3] Root Directory: $PSScriptRoot" -ForegroundColor Gray
Write-Host "[2/3] Dashboard URL:  http://localhost:$Port" -ForegroundColor Cyan
Write-Host "[3/3] REST API URL:   http://localhost:$ApiPort" -ForegroundColor Cyan
Write-Host ""

# 2. Check and cleanly free the target port if occupied by a previous background process
try {
    $busy = Get-NetTCPConnection -LocalPort $Port -ErrorAction SilentlyContinue
    if ($busy) {
        $pids = $busy.OwningProcess | Select-Object -Unique
        foreach ($p in $pids) {
            if ($p -and $p -ne 0) {
                Write-Host "Port $Port is occupied by PID $p. Freeing port..." -ForegroundColor Yellow
                Stop-Process -Id $p -Force -ErrorAction SilentlyContinue
            }
        }
        Start-Sleep -Milliseconds 700
    }
} catch {
    # Non-admin or connection lookup fallback
}

# 3. Open browser automatically to the exact active port
Start-Process "http://localhost:$Port"

# 4. Launch Streamlit bound to 0.0.0.0 (accessible everywhere on LAN/Wi-Fi)
Write-Host "Launching Streamlit server on 0.0.0.0:$Port..." -ForegroundColor Green
& "$PSScriptRoot\venv\Scripts\python.exe" -m streamlit run frontend/app.py --server.port $Port --server.address 0.0.0.0
