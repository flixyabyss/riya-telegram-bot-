@echo off
title Riya - Telegram AI Group Manager Bot
color 0D
echo ========================================================
echo       🌸 RIYA - AI TELEGRAM GROUP MANAGER BOT 🌸
echo ========================================================
echo.

cd /d "%~dp0"

echo [1/2] Checking and installing dependencies...
python -m pip install -r requirements.txt --quiet --upgrade
if %errorlevel% neq 0 (
    echo.
    echo [!] Failed to install dependencies. Please ensure Python is in your PATH.
    pause
    exit /b %errorlevel%
)

echo [2/2] Launching Riya...
echo.
python bot.py

pause
