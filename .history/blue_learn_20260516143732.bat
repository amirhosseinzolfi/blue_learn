@echo off
if "%1"=="run" goto run

:: Re-launch this bat hidden via wscript (no terminal window)
echo Set sh=CreateObject("WScript.Shell") > "%TEMP%\bl_run.vbs"
echo sh.Run "cmd /c ""%~f0"" run", 0, False >> "%TEMP%\bl_run.vbs"
wscript.exe /nologo "%TEMP%\bl_run.vbs"
del "%TEMP%\bl_run.vbs" >nul 2>&1
exit

:run
cd /d "D:\Documents\programming projects\blue_learn"
start "" /b ".venv\Scripts\python.exe" -m uvicorn main:app --reload --port 8083
timeout /t 3 /nobreak >nul
start msedge --app=http://localhost:8083
