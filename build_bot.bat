@echo off
cd /d "%~dp0bot"
pip uninstall -y python-telegram-bot 2>NUL
pip install -r requirements.txt
pyinstaller --noconfirm --onefile --windowed --name TelegramBot bot.py
@echo Build complete. Executable is in dist folder.
