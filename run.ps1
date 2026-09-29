Write-Host "===================================================" -ForegroundColor Green
Write-Host "  Faslyn - BRICS AgriN Intelligence Platform" -ForegroundColor Green
Write-Host "===================================================" -ForegroundColor Green
Write-Host ""
Write-Host "Starting Faslyn Dashboard and REST API..." -ForegroundColor Cyan
Write-Host "Dashboard URL: http://localhost:8501" -ForegroundColor Yellow
Write-Host "REST API URL:  http://localhost:8000" -ForegroundColor Yellow
Write-Host ""
& ".\venv\Scripts\python.exe" -m streamlit run frontend/app.py
