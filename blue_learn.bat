@echo off

cd /d "D:\Documents\programming projects\blue_learn"

:: Start the server using the .venv python directly
start "" /b ".venv\Scripts\python.exe" -m uvicorn main:app --reload --port 8083

:: Wait for server to initialize
timeout /t 3 /nobreak >nul

:: Launch as Chrome app window
:: start chrome --app=http://localhost:8083

:: Minimize the terminal window
".venv\Scripts\python.exe" -c "import ctypes; hwnd = ctypes.windll.kernel32.GetConsoleWindow(); ctypes.windll.user32.ShowWindow(hwnd, 6)"