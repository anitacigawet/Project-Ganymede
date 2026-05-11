@echo off
REM ────────────────────────────────────────────────────────────────────
REM  Project Ganymede — dev launcher
REM
REM  Double-click this file to start the backend.
REM  Close this window to stop the server. That's it.
REM
REM  - Activates the Python 3.12 venv at ganymede-backend\venv_312
REM  - Finds a free port starting at 8000 (falls through to 8010 if busy)
REM  - Launches uvicorn with --reload, bound to 127.0.0.1
REM  - Closing this window sends a stop signal to uvicorn (graceful shutdown)
REM ────────────────────────────────────────────────────────────────────

setlocal enabledelayedexpansion

title Project Ganymede - backend

cd /d "%~dp0ganymede-backend"

if not exist "venv_312\Scripts\activate.bat" (
    echo.
    echo  ERROR: Python 3.12 venv not found.
    echo  Expected: %CD%\venv_312\Scripts\activate.bat
    echo.
    echo  Set up the venv first per the README, then re-run this script.
    echo.
    pause
    exit /b 1
)

call "venv_312\Scripts\activate.bat"
set "PYTHONPATH=."

REM ── Port discovery ─────────────────────────────────────────────────
REM  Try 8000 first. If busy, walk up to 8010 looking for a free port.
REM  Python is on PATH via the venv we just activated, so we use it to
REM  test bindability — most reliable check on Windows.

set PORT=8000
set MAXPORT=8010

:checkport
python -c "import socket,sys; s=socket.socket(); s.bind(('127.0.0.1',%PORT%)); s.close()" 2>nul
if errorlevel 1 (
    set /a PORT+=1
    if !PORT! gtr %MAXPORT% (
        echo.
        echo  ERROR: No free port found between 8000 and %MAXPORT%.
        echo  Close whatever is listening on those ports and re-run.
        echo.
        pause
        exit /b 1
    )
    goto checkport
)

if not "%PORT%"=="8000" (
    echo.
    echo  Default port 8000 was busy; using %PORT% instead.
)

echo.
echo  ====================================================
echo   Project Ganymede backend
echo.
echo   Listening on  http://127.0.0.1:%PORT%
echo   Health check  http://127.0.0.1:%PORT%/api/v2/health
echo.
echo   Close this window to stop the server.
echo  ====================================================
echo.

REM  uvicorn runs in the foreground in this same cmd window. Closing the
REM  window sends CTRL_CLOSE_EVENT to the process; uvicorn handles it as
REM  a clean shutdown. No detached process to track down later.

uvicorn app.main:app --reload --host 127.0.0.1 --port %PORT%

REM  Once uvicorn exits (clean shutdown, error, or window close), control
REM  returns here. The venv stays activated for this dying shell. Nothing
REM  to clean up.

endlocal
