@echo off
echo Running database migration for Windows...
python run_migration.py
if %ERRORLEVEL% NEQ 0 (
    echo Migration failed with error code %ERRORLEVEL%
    pause
    exit /b %ERRORLEVEL%
)
echo Migration completed successfully
pause