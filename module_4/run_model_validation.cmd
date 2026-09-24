@echo off
setlocal
title Module 4 - SQLAlchemy Model Validation
cd /d "%~dp0"

if not exist ".venv\Scripts\python.exe" (
    echo The module_4 virtual environment was not found.
    pause
    exit /b 1
)

echo Validating the SQLAlchemy Applicant model against PostgreSQL...
echo Your password will not appear while you type it.
echo.
set "PYTHONPATH=%CD%\src"
".venv\Scripts\python.exe" tools\validate_models.py
set "validation_status=%ERRORLEVEL%"
echo.

if not "%validation_status%"=="0" (
    echo SQLAlchemy model validation did not complete successfully.
) else (
    echo SQLAlchemy model validation completed successfully.
)

pause
exit /b %validation_status%
