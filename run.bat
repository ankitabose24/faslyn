@echo off
setlocal enabledelayedexpansion
title Faslyn - Agricultural Intelligence Network

:: 1. Navigate to script directory so it can be executed from anywhere
cd /d "%~dp0"

:: 2. Configurable ports (Pass as arguments or use defaults)
:: Usage: run.bat [UI_PORT] [API_PORT]
set "PORT=%~1"
if "%PORT%"=="" set "PORT=8501"

set "API_PORT=%~2"
if "%API_PORT%"=="" set "API_PORT=8000"
set "FASLYN_API_PORT=%API_PORT%"

echo ===================================================
echo   Faslyn - BRICS AgriN Intelligence Platform
echo ===================================================
echo.
echo [1/3] Root Directory: %~dp0
echo [2/3] Dashboard URL:  http://localhost:%PORT%
echo [3/3] REST API URL:   http://localhost:%API_PORT%
echo.

:: 3. Free port if currently occupied by a previous zombie process
for /f "tokens=5" %%a in ('netstat -aon ^| findstr ":%PORT% "') do (
    if not "%%a"=="" if not "%%a"=="0" (
        echo Port %PORT% is currently occupied by PID %%a. Freeing port...
        taskkill /F /PID %%a >nul 2>&1
        timeout /t 1 /nobreak >nul
    )
)

:: 4. Launch default browser to the active port
start "" "http://localhost:%PORT%"

:: 5. Launch Streamlit explicitly on the chosen port and bind to 0.0.0.0 (accessible everywhere)
echo Starting Streamlit server on 0.0.0.0:%PORT%...
.\venv\Scripts\python.exe -m streamlit run frontend/app.py --server.port %PORT% --server.address 0.0.0.0
pause
