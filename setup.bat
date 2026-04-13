@echo off
setlocal enabledelayedexpansion

echo.
echo  ====================================================
echo      lagomrost - Voice Cloner Setup
echo  ====================================================
echo.
echo  This will install everything you need. Just wait.
echo.

:: ---- Check Python ----
:: Try py launcher with 3.12 first, then 3.11, then 3.10, then fall back to python
set "PYTHON_CMD="
for %%V in (3.12 3.11 3.10) do (
    if not defined PYTHON_CMD (
        py -%%V --version >nul 2>&1
        if not errorlevel 1 set "PYTHON_CMD=py -%%V"
    )
)
if not defined PYTHON_CMD (
    python --version >nul 2>&1
    if errorlevel 1 (
        echo  [ERROR] Python not found!
        echo.
        echo  Install Python 3.10-3.12 from https://python.org
        echo  Make sure to check "Add Python to PATH" during install.
        echo.
        pause
        exit /b 1
    )
    set "PYTHON_CMD=python"
)

:: Verify version is 3.10-3.12
for /f "tokens=2 delims= " %%a in ('%PYTHON_CMD% --version 2^>^&1') do set "PYVER=%%a"
for /f "tokens=1,2 delims=." %%a in ("%PYVER%") do (
    set "PYMAJOR=%%a"
    set "PYMINOR=%%b"
)
if %PYMAJOR% NEQ 3 (
    echo  [ERROR] Python %PYVER% is not supported.
    echo  Install Python 3.10-3.12 from https://python.org
    pause
    exit /b 1
)
if %PYMINOR% LSS 10 (
    echo  [ERROR] Python %PYVER% is too old.
    echo  Install Python 3.10-3.12 from https://python.org
    pause
    exit /b 1
)
if %PYMINOR% GTR 12 (
    echo  [ERROR] Python %PYVER% is too new ^(PyTorch doesn't support it yet^).
    echo  Install Python 3.10-3.12 from https://python.org
    echo  Tip: If you have multiple versions, the setup will auto-detect 3.10-3.12 via "py" launcher.
    pause
    exit /b 1
)
echo  [OK] Python %PYVER% found (using: %PYTHON_CMD%)

:: ---- Create virtual environment ----
if not exist "venv\Scripts\python.exe" (
    echo.
    echo  [1/5] Creating virtual environment...
    %PYTHON_CMD% -m venv venv
    if errorlevel 1 (
        echo  [ERROR] Failed to create virtual environment.
        pause
        exit /b 1
    )
) else (
    echo  [OK] Virtual environment exists
)

:: Activate
call venv\Scripts\activate.bat

:: ---- Install PyTorch ----
echo.
echo  [2/5] Installing PyTorch...

:: Check for NVIDIA GPU
nvidia-smi >nul 2>&1
if errorlevel 1 (
    echo        No NVIDIA GPU detected - installing CPU version
    pip install torch torchaudio --index-url https://download.pytorch.org/whl/cpu --quiet
) else (
    echo        NVIDIA GPU detected - installing CUDA version
    pip install torch torchaudio --index-url https://download.pytorch.org/whl/cu121 --quiet
)

:: ---- Install dependencies ----
echo.
echo  [3/5] Installing dependencies...
pip install -r requirements.txt --quiet

:: ---- Check FFmpeg ----
echo.
echo  [4/5] Checking FFmpeg...
ffmpeg -version >nul 2>&1
if errorlevel 1 (
    echo        FFmpeg not found - installing via pip...
    pip install ffmpeg-python --quiet
    echo        NOTE: You may still need FFmpeg in your PATH.
    echo        Download from https://ffmpeg.org/download.html
) else (
    echo        [OK] FFmpeg found
)

:: ---- Download models ----
echo.
echo  [5/5] Downloading AI models...
if not exist "OpenVoice\checkpoints_v2\converter\checkpoint.pth" (
    pip install huggingface_hub --quiet
    python -c "from huggingface_hub import snapshot_download; snapshot_download('myshell-ai/OpenVoiceV2', local_dir='OpenVoice/checkpoints_v2')"
    if errorlevel 1 (
        echo  [ERROR] Model download failed. Check your internet connection.
        pause
        exit /b 1
    )
) else (
    echo        [OK] Models already downloaded
)

:: ---- Create directories ----
if not exist "references" mkdir references
if not exist "output" mkdir output

:: ---- Verify ----
echo.
echo  ====================================================
echo      Verifying installation...
echo  ====================================================
echo.

python -c "import torch; print(f'  PyTorch {torch.__version__} - CUDA: {torch.cuda.is_available()}'); import librosa; print(f'  Librosa {librosa.__version__}'); import sys; sys.path.insert(0,'OpenVoice'); from openvoice.api import ToneColorConverter; print('  OpenVoice: OK')"

if errorlevel 1 (
    echo.
    echo  [ERROR] Verification failed. See errors above.
    echo  Check SETUP.md for troubleshooting.
    pause
    exit /b 1
)

echo.
echo  ====================================================
echo      Setup complete!
echo  ====================================================
echo.
echo  To use, first activate the environment:
echo.
echo    venv\Scripts\activate
echo.
echo  Then clone a voice:
echo.
echo    python tools\clone_voice.py -r my_voice.wav -i song.mp3 -o output.wav
echo.
echo  Or separate a song first:
echo.
echo    python tools\separate.py -i song.mp3
echo.
pause
