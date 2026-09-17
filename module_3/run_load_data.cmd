@echo off
setlocal
title Module 3 - Load GradCafe Data
cd /d "%~dp0"

if not exist ".venv\Scripts\python.exe" (
    echo The module_3 virtual environment was not found.
    echo Run: python -m venv .venv
    pause
    exit /b 1
)

echo Loading the cleaned Module 2 data into PostgreSQL...
echo Your password will not appear while you type it.
echo.
".venv\Scripts\python.exe" load_data.py
set "loader_status=%ERRORLEVEL%"
echo.

if not "%loader_status%"=="0" (
    echo The loader did not complete successfully.
) else (
    echo Part 1 loader completed successfully.
)

pause
exit /b %loader_status%
