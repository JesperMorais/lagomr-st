@echo off
echo ============================================
echo  Voice Cloner - Setup
echo ============================================
echo.

:: Check Python
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python not found. Install Python 3.10-3.12 from python.org
    pause
    exit /b 1
)

:: Show Python version
for /f "tokens=*" %%i in ('python --version 2^>^&1') do echo Found: %%i

:: Create virtual environment
if not exist "Scripts\python.exe" (
    echo.
    echo Creating virtual environment...
    python -m venv .
) else (
    echo Virtual environment already exists.
)

:: Activate
call Scripts\activate.bat

:: Install PyTorch with CUDA
echo.
echo Installing PyTorch with CUDA 12.1...
pip install torch torchaudio --index-url https://download.pytorch.org/whl/cu121

:: Install dependencies
echo.
echo Installing dependencies...
pip install -r requirements.txt

:: Download model checkpoints if missing
if not exist "OpenVoice\checkpoints_v2\converter\checkpoint.pth" (
    echo.
    echo Downloading OpenVoice V2 model checkpoints...
    pip install huggingface_hub
    python -c "from huggingface_hub import snapshot_download; snapshot_download('myshell-ai/OpenVoiceV2', local_dir='OpenVoice/checkpoints_v2')"
) else (
    echo Model checkpoints already present.
)

:: Create directories
if not exist "references" mkdir references
if not exist "output" mkdir output

:: Verify
echo.
echo ============================================
echo  Verifying installation...
echo ============================================
python -c "import torch; print(f'PyTorch {torch.__version__} - CUDA: {torch.cuda.is_available()}'); import librosa; print(f'Librosa {librosa.__version__}'); import sys; sys.path.insert(0,'OpenVoice'); from openvoice.api import ToneColorConverter; print('OpenVoice: OK'); print(); print('Setup complete!')"

if errorlevel 1 (
    echo.
    echo WARNING: Verification failed. Check the errors above.
    echo See SETUP.md for troubleshooting.
) else (
    echo.
    echo ============================================
    echo  Ready! Try:
    echo    python tools\clone_voice.py -r reference.wav -i song.mp3 -o output.wav
    echo ============================================
)

pause
