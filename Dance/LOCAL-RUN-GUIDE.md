# Local Run Guide for Testers

## What you need

1. A complete copy of this project folder, including `client`, `server`, `package.json`, and the startup scripts.
2. Node.js LTS installed from [nodejs.org](https://nodejs.org/).
3. Google Chrome or Microsoft Edge. VS Code is recommended but Visual Studio is not required.

## Start in VS Code

1. Extract the complete project folder to a local location.
2. Open that folder in VS Code.
3. Open the integrated terminal with **Terminal → New Terminal**.
4. Run one of the following commands:

```powershell
.\start-local.bat
```

or:

```powershell
powershell -ExecutionPolicy Bypass -File .\start-local.ps1
```

The first run downloads dependencies automatically. When the terminal reports that the frontend is ready, open [http://localhost:5173](http://localhost:5173).

## Stop the system

Return to the terminal and press `Ctrl+C`.

## Important testing notes

- The app runs locally; `localhost` can be accessed only from the same computer.
- Camera testing requires the tester to grant browser camera permission.
- For the full workflow, use a local MP4 with one visible full-body subject, preferably 10–60 seconds long.
- Do not send the `node_modules` or `dist` folders when sharing the project. The startup script recreates dependencies automatically.
