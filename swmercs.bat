@echo off
setlocal
cd /d "%~dp0"
if exist ".venv\Scripts\python.exe" (
    ".venv\Scripts\python.exe" swmercs.py
) else if exist "star-map-editor\.venv\Scripts\python.exe" (
    "star-map-editor\.venv\Scripts\python.exe" swmercs.py
) else (
    where py >nul 2>&1
    if not errorlevel 1 (
        py -3 swmercs.py
    ) else (
        python swmercs.py
    )
)
if errorlevel 1 (
    echo.
    echo SW-Mercs could not start. Check the error above and try again.
    pause
    exit /b 1
)

