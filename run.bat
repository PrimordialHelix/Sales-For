@echo off
setlocal

cd /d "%~dp0"
if errorlevel 1 (
    echo ERROR: Could not switch to the project directory.
    pause
    exit /b 1
)

if not exist ".venv\Scripts\python.exe" (
    echo ERROR: Project setup has not been run yet.
    echo Run requirements.bat once, then run this file again.
    pause
    exit /b 1
)

echo Starting the sales forecasting dashboard...
".venv\Scripts\python.exe" -m streamlit run app.py
if errorlevel 1 (
    echo ERROR: The dashboard exited with an error.
    pause
    exit /b 1
)

exit /b 0
