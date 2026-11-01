@echo off
setlocal
cd /d "%~dp0"

where node >nul 2>nul
if errorlevel 1 (
  echo [ERROR] Node.js was not found.
  echo Please install Node.js LTS from https://nodejs.org/ and run this script again.
  pause
  exit /b 1
)

if not exist "node_modules" (
  echo Installing project dependencies. This may take a few minutes on the first run...
  call npm install
  if errorlevel 1 (
    echo [ERROR] Dependency installation failed.
    pause
    exit /b 1
  )
)

echo.
echo Starting the local teaching system...
echo Open http://localhost:5173 in a browser after the server starts.
echo Press Ctrl+C in this window to stop the system.
echo.
call npm run dev
pause
