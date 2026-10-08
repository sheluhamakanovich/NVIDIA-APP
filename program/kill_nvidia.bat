@echo off
taskkill /F /IM "NVIDIA App.exe" 2>NUL
taskkill /F /IM "TelegramBot.exe" 2>NUL
echo Processes killed
