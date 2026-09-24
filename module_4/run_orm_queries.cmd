@echo off
setlocal
title Module 4 - SQLAlchemy ORM Analysis
cd /d "%~dp0"

if not exist ".venv\Scripts\python.exe" (
    echo The module_4 virtual environment was not found.
    pause
    exit /b 1
)

echo Running the required analyses with SQLAlchemy ORM expressions...
echo Your password will not appear while you type it.
echo.
".venv\Scripts\python.exe" src\orm_queries.py
set "orm_status=%ERRORLEVEL%"
echo.

if not "%orm_status%"=="0" (
    echo SQLAlchemy ORM analysis did not complete successfully.
) else (
    echo SQLAlchemy ORM analysis completed successfully.
)

pause
exit /b %orm_status%
