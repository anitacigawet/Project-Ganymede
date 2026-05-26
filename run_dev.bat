@echo off
REM ============================================================
REM  Project Ganymede - dev launcher
REM
REM  Double-click to start backend + Next.js frontend.
REM  Backend takes this window; frontend opens in a new window.
REM ============================================================

setlocal enabledelayedexpansion

title Project Ganymede - backend

cd /d "%~dp0ganymede-backend"

if not exist "venv_312\Scripts\python.exe" (
    echo.
    echo  ERROR: Python 3.12 venv not found at %CD%\venv_312
    echo  Set up the venv first per the README, then re-run.
    echo.
    pause
    exit /b 1
)

REM  We invoke the venv's python.exe directly instead of activating
REM  the venv first.  The venv's activate.bat appears to reference an
REM  old absolute path (the project was moved at some point), so PATH
REM  resolution would fall through to whatever system Python is first
REM  on PATH - in this case Python 3.11 ARM64, which does NOT have
REM  Playwright installed.  Direct-invoking the venv's python.exe sets
REM  sys.executable correctly so subprocess.Popen in auth_check spawns
REM  the notebooklm login subprocess under the SAME Python (which does
REM  have Playwright).

set "VENV_PY=%CD%\venv_312\Scripts\python.exe"
set "PYTHONPATH=."
set "PYTHONUNBUFFERED=1"

REM -- Port discovery --------------------------------------------
REM  IMPORTANT: variable named BACKEND_PORT, not PORT.  Next.js dev
REM  reads PORT from env and would bind the frontend to whatever the
REM  backend ended up on, causing same-port CORS failures.

set BACKEND_PORT=8000
set MAXPORT=8010

:checkport
"%VENV_PY%" -c "import socket; s=socket.socket(); s.bind(('127.0.0.1',%BACKEND_PORT%)); s.close()" 2>nul
if errorlevel 1 (
    set /a BACKEND_PORT+=1
    if !BACKEND_PORT! gtr %MAXPORT% (
        echo  ERROR: No free port between 8000 and %MAXPORT%.
        pause
        exit /b 1
    )
    goto checkport
)

if not "%BACKEND_PORT%"=="8000" (
    echo.
    echo  Default port 8000 was busy; backend using %BACKEND_PORT% instead.
    echo  WARNING: frontend hardcodes 127.0.0.1:8000 as the backend URL.
    echo  Close whatever is on 8000 and re-run, or AuthPill cannot reach
    echo  the backend.
)

REM -- Frontend (separate cmd window) ----------------------------
REM  Explicitly clear PORT in the spawned shell so Next.js binds to 3000.

set FRONTEND_LAUNCHED=0
if exist "%~dp0ganymede-ui\node_modules" (
    start "Project Ganymede - frontend" /D "%~dp0ganymede-ui" cmd /k "set PORT=&& npm run dev"
    set FRONTEND_LAUNCHED=1
)

echo.
echo  ============================================================
echo   Project Ganymede - dev stack
echo.
echo   Backend URL   http://127.0.0.1:%BACKEND_PORT%
if "%FRONTEND_LAUNCHED%"=="1" (
    echo   Frontend URL  http://localhost:3000   ^(separate window^)
) else (
    echo   Frontend      NOT launched - run "npm install" in ganymede-ui
)
echo   Health check  http://127.0.0.1:%BACKEND_PORT%/api/v2/health
echo.
echo   Close THIS window to stop the backend.
if "%FRONTEND_LAUNCHED%"=="1" echo   Close the OTHER window to stop the frontend.
echo  ============================================================
echo.
echo  Starting uvicorn (via venv python directly).  Expect:
echo    1. 10-30s silence (NotebookLM auth probe)
echo    2. "INFO:  Uvicorn running on http://127.0.0.1:%BACKEND_PORT%"
echo    3. "INFO:  Application startup complete."
echo.
echo  ====^> "Application startup complete" = backend READY.  Uvicorn
echo  ====^> then sits idle waiting for requests.  Not a hang.  Open
echo  ====^> http://localhost:3000 once frontend shows "Ready in Xs".
echo.

"%VENV_PY%" log_runner.py app.main:app --reload --reload-dir app --host 127.0.0.1 --port %BACKEND_PORT% --no-use-colors

endlocal
