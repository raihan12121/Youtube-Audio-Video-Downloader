@echo off
title YouTube Downloader Pro
cd /d "%~dp0"

echo ========================================================
echo    YouTube Video, Audio & Bulk Downloader Pro v2.0
echo ========================================================
echo.

if exist "release\win-unpacked\YouTube Downloader Pro.exe" (
    echo Starting Windows Desktop Application...
    start "" "release\win-unpacked\YouTube Downloader Pro.exe"
    exit /b 0
)

if not exist "dist\index.html" (
    echo Building application interface...
    call npm run build:vite
)

echo Launching Electron Desktop Window...
start "" npx electron .
exit /b 0
