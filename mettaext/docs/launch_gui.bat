@echo off
REM EngAIn Narrative Pipeline GUI Launcher (Windows)

echo ================================================
echo   EngAIn Narrative Pipeline GUI
echo   AI Logic Built for AI, Not Humans
echo ================================================
echo.

REM Check for Python
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python not found
    echo Please install Python 3 from https://www.python.org/
    pause
    exit /b 1
)

echo Python found
echo.
echo Launching GUI...
echo.

REM Launch the GUI
python narrative_pipeline_gui.py

echo.
echo GUI closed.
pause
