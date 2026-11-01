$ErrorActionPreference = 'Stop'
Set-Location $PSScriptRoot

if (-not (Get-Command node -ErrorAction SilentlyContinue)) {
  Write-Host '[ERROR] Node.js was not found.' -ForegroundColor Red
  Write-Host 'Install Node.js LTS from https://nodejs.org/ and run this script again.'
  exit 1
}

if (-not (Test-Path 'node_modules')) {
  Write-Host 'Installing project dependencies. This may take a few minutes on the first run...' -ForegroundColor Yellow
  npm install
  if ($LASTEXITCODE -ne 0) { throw 'Dependency installation failed.' }
}

Write-Host ''
Write-Host 'Starting the local teaching system...' -ForegroundColor Green
Write-Host 'Open http://localhost:5173 in a browser after the server starts.'
Write-Host 'Press Ctrl+C in this terminal to stop the system.'
npm run dev
