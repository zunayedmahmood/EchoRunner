@echo off
setlocal
cd /d "%~dp0\.."
if not exist .venv\Scripts\activate.bat (
  echo Virtual environment not found. Run scripts\setup_venv.ps1 first.
  exit /b 1
)
call .venv\Scripts\activate.bat
python -m echorunner --tutorial --trainer
