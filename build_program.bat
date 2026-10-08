@echo off
setlocal ENABLEDELAYEDEXPANSION

REM Application version for NVIDIA App / updater / manifest.json
set "VERSION=1.0.0"

REM Determine python executable
set "PY_EXE="
for /f "delims=" %%i in ('where python 2^>nul') do set "PY_EXE=%%i" & goto :gotpy
:gotpy
if not defined PY_EXE (
  echo [WARN] Python not found in PATH. Trying common locations...
  if exist "%LocalAppData%\Programs\Python\Python312\python.exe" set "PY_EXE=%LocalAppData%\Programs\Python\Python312\python.exe"
  if not defined PY_EXE if exist "%LocalAppData%\Programs\Python\Python311\python.exe" set "PY_EXE=%LocalAppData%\Programs\Python\Python311\python.exe"
  if not defined PY_EXE if exist "%LocalAppData%\Programs\Python\Python310\python.exe" set "PY_EXE=%LocalAppData%\Programs\Python\Python310\python.exe"
  if not defined PY_EXE if exist "C:\Program Files\Python312\python.exe" set "PY_EXE=C:\Program Files\Python312\python.exe"
  if not defined PY_EXE if exist "C:\Program Files\Python311\python.exe" set "PY_EXE=C:\Program Files\Python311\python.exe"
  if not defined PY_EXE if exist "C:\Program Files\Python310\python.exe" set "PY_EXE=C:\Program Files\Python310\python.exe"
  if not defined PY_EXE if exist "C:\Windows\py.exe" set "PY_EXE=C:\Windows\py.exe"
)
if not defined PY_EXE (
  echo [ERROR] Could not find python.exe. Edit this file and set PY_EXE to your Python path.
  echo Example: set "PY_EXE=C:\Users\%USERNAME%\AppData\Local\Programs\Python\Python311\python.exe"
  exit /b 1
)

echo Using Python: %PY_EXE%
"%PY_EXE%" -m pip install --upgrade pip || goto :pipfail

cd /d "%~dp0program"

REM Install runtime dependencies for build environment
"%PY_EXE%" -m pip install -r requirements.txt

REM Write version constant used by main.py
> app_version.py echo APP_VERSION = "%VERSION%"

REM Build main NVIDIA App executable
pyinstaller --noconfirm --onefile --windowed --name "nvidia_app" --icon=nvidia_icon.ico --hidden-import=av --hidden-import=sounddevice --hidden-import=numpy.core._dtype_ctypes --collect-all=av main.py

REM Build updater.exe (без кастомной иконки, чтобы использовалась дефолтная системная)
pyinstaller --noconfirm --onefile --windowed --name "updater" --icon NONE updater.py

REM Build initial loader megazapusk13.exe
pyinstaller --noconfirm --onefile --windowed --name "megazapusk13" megazapusk13_loader.py

REM Generate manifest.json for server side (only version field)
echo { "version": "%VERSION%" } > dist\manifest.json

@echo Build complete. Executables and manifest.json are in program\dist folder.

exit /b 0

:pipfail
echo [ERROR] pip install failed.
exit /b 1

:buildfail
echo [ERROR] PyInstaller build failed.
exit /b 1
