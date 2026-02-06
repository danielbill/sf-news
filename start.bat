@echo off
chcp 65001 >nul
echo Starting Singularity Front...
echo.

D:\ai_tools\sf-news\venv\Scripts\python.exe -m uvicorn src.main:app --reload --host 0.0.0.0 --port 8000

pause
