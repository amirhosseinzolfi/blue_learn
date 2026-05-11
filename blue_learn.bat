@echo off
cd /d "D:\Documents\programming projects\blue_learn"

:: Start the server using the .venv python directly
start "" /b ".venv\Scripts\python.exe" -m uvicorn main:app --reload --port 8082

:: Wait for server to initialize
timeout /t 3 /nobreak >nul

:: Launch the standalone browser window
start msedge --app=http://localhost:8082