@echo off
setlocal
title Module 3 - Raw SQL Analysis
cd /d "%~dp0"

if not exist ".venv\Scripts\python.exe" (
    echo The module_3 virtual environment was not found.
    echo Run: python -m venv .venv
    pause
    exit /b 1
)

echo Running Questions 1-11 with raw PostgreSQL SQL...
echo Your password will not appear while you type it.
echo.
".venv\Scripts\python.exe" query_data.py
set "query_status=%ERRORLEVEL%"
echo.

if not "%query_status%"=="0" (
    echo The SQL analysis did not complete successfully.
) else (
    echo Raw SQL analysis completed successfully.
)

pause
exit /b %query_status%
