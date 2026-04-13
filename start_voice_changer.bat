@echo off
title Voice Changer
echo ============================================
echo   Voice Changer - Starting Web UI...
echo ============================================
echo.

:: Activate virtual environment
if exist "venv\Scripts\activate.bat" (
    call venv\Scripts\activate.bat
) else (
    echo [WARNING] Virtual environment not found. Run setup.bat first.
    pause
    exit /b 1
)

:: Check that gradio is installed
python -c "import gradio" 2>nul
if errorlevel 1 (
    echo Installing Gradio...
    pip install gradio
)

:: Launch the web UI
echo Starting on http://localhost:7860
echo.
python tools\voice_changer_app.py %*

pause
