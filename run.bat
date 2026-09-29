@echo off
title Faslyn - Agricultural Intelligence Network
echo ===================================================
echo   Faslyn - BRICS AgriN Intelligence Platform
echo ===================================================
echo.
echo Starting Faslyn Dashboard and REST API...
echo Dashboard URL: http://localhost:8501
echo REST API URL:  http://localhost:8000
echo.
.\venv\Scripts\python.exe -m streamlit run frontend/app.py
pause
