@echo off
REM ============================================================================
REM run_viewer.bat -- Render Project Ganymede docs in the canvas viewer.
REM
REM Two-step pipeline:
REM   [1/2] scripts\build_canvas.py regenerates canvas_data.json +
REM         file_contents.json from docs/ into the viewer's public/ folder.
REM   [2/2] npm run dev in the viewer folder starts Vite (default port 5173).
REM
REM Re-run any time docs/ changes to refresh the canvas. Press Ctrl+C in this
REM window to stop the server.
REM
REM The viewer itself lives at Desktop\ganymede docs\ganymede-viewer\.
REM This batch resolves that path relative to its own location.
REM ============================================================================

setlocal

set "PROJECT_ROOT=%~dp0"
if "%PROJECT_ROOT:~-1%"=="\" set "PROJECT_ROOT=%PROJECT_ROOT:~0,-1%"

REM Resolve the viewer folder (three levels up from Project Ganymede -> Desktop).
for %%I in ("%PROJECT_ROOT%\..\..\..\ganymede docs\ganymede-viewer") do set "VIEWER_DIR=%%~fI"

echo.
echo === Ganymede Canvas Viewer ===
echo  Project:  %PROJECT_ROOT%
echo  Viewer:   %VIEWER_DIR%
echo.

if not exist "%VIEWER_DIR%\package.json" (
    echo [ERROR] Viewer not found at:
    echo         %VIEWER_DIR%
    echo.
    echo Adjust the relative path in this batch if you moved the viewer.
    pause
    exit /b 1
)

REM -----------------------------------------------------------------
REM [1/2] Regenerate canvas data from docs/.
REM -----------------------------------------------------------------
echo [1/2] Regenerating canvas_data.json + file_contents.json from docs/...
pushd "%PROJECT_ROOT%"
python scripts\build_canvas.py
if errorlevel 1 (
    echo.
    echo [ERROR] scripts\build_canvas.py failed. See output above.
    popd
    pause
    exit /b 1
)
popd
echo.

REM -----------------------------------------------------------------
REM [2/2] Launch the Vite dev server (stays in this window).
REM -----------------------------------------------------------------
echo [2/2] Starting Vite dev server. Open http://localhost:5173/ once it boots.
echo        Press Ctrl+C in this window to stop.
echo.

pushd "%VIEWER_DIR%"
call npm run dev
popd

endlocal
