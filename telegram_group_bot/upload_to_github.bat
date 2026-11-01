@echo off
title Push Riya Bot to GitHub
color 0B
echo ========================================================
echo         🌸 UPLOADING RIYA BOT TO GITHUB 🌸
echo ========================================================
echo.
echo Target Repository: https://github.com/flixyabyss/riya-telegram-bot-
echo.

set PATH=%PATH%;C:\Users\famil\AppData\Local\Programs\MinGit\cmd

cd /d "%~dp0"

echo [*] Pushing files to main branch...
echo [*] If prompted, sign in to your GitHub account in the pop-up window.
echo.
git push -u origin main

if %errorlevel% equ 0 (
    echo.
    echo ========================================================
    echo  🎉 SUCCESS! Your bot is now uploaded to GitHub! 🌸
    echo  👉 View it at: https://github.com/flixyabyss/riya-telegram-bot-
    echo ========================================================
) else (
    echo.
    echo [!] Push failed or cancelled. If you see a login prompt, please enter your GitHub credentials.
)

pause
