@echo off
setlocal
title Module 3 - Flask Analysis
cd /d "%~dp0"

if not exist ".venv\Scripts\python.exe" (
    echo The module_3 virtual environment was not found.
    pause
    exit /b 1
)

echo Starting the dynamic Flask analysis page...
echo Your password will not appear while you type it.
echo.
".venv\Scripts\python.exe" run_flask.py
set "flask_status=%ERRORLEVEL%"
echo.
echo Flask stopped with status %flask_status%.
pause
exit /b %flask_status%
