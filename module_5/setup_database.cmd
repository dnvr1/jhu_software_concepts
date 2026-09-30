@echo off
setlocal
cd /d "%~dp0"
echo Module 5 database setup
echo You will enter the PostgreSQL administrator password, then a new
echo password for gradcafe_app twice. Passwords will not be displayed.
echo This creates a NEW gradcafe_app role in the existing gradcafe database.
echo.
"C:\Program Files\PostgreSQL\17\bin\psql.exe" -h localhost -U postgres -d gradcafe -W -f least_privilege.sql -f verify_privileges.sql > database_privileges.txt
if errorlevel 1 (
    echo Setup did not finish. Keep the error above and tell Codex.
) else (
    type database_privileges.txt
    echo Verification saved in database_privileges.txt.
)
pause
