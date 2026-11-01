@echo off
setlocal
cd /d "%~dp0"
set "PYTHON_CMD=python"
if exist "%USERPROFILE%\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe" set "PYTHON_CMD=%USERPROFILE%\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe"
py -3.12 --version >nul 2>nul && set "PYTHON_CMD=py -3.12"
if not exist ".venv\Scripts\python.exe" (
  echo First launch: preparing Fancam Maker...
  call %PYTHON_CMD% -m venv .venv
  call .venv\Scripts\python.exe -m pip install --upgrade pip
)
call .venv\Scripts\python.exe -m pip install -r requirements.txt --disable-pip-version-check -q
call .venv\Scripts\python.exe main.py
endlocal
