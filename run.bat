@echo off
echo ==============================================
echo       Starting TrueEyeball Project
echo ==============================================

if exist venv\Scripts\activate (
    echo [~] Activating virtual environment...
    call venv\Scripts\activate
) else if exist .venv\Scripts\activate (
    echo [~] Activating virtual environment...
    call .venv\Scripts\activate
) else (
    echo [!] Virtual environment not found. Ensure dependencies are installed.
)

python main.py

if %ERRORLEVEL% neq 0 (
    echo.
    echo [!] Application exited with an error. 
    pause
)
