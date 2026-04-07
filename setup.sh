#!/usr/bin/env bash
set -e

echo ""
echo " ===================================================="
echo "     lagomrost - Voice Cloner Setup"
echo " ===================================================="
echo ""
echo " This will install everything you need. Just wait."
echo ""

# ---- Check Python ----
if ! command -v python3 &> /dev/null; then
    echo " [ERROR] Python 3 not found!"
    echo ""
    echo " Install Python 3.10-3.12:"
    echo "   Ubuntu/Debian: sudo apt install python3 python3-venv python3-pip"
    echo "   macOS:         brew install python@3.12"
    echo ""
    exit 1
fi

PYTHON=python3
echo " [OK] $($PYTHON --version) found"

# ---- Create virtual environment ----
if [ ! -f "venv/bin/activate" ]; then
    echo ""
    echo " [1/5] Creating virtual environment..."
    $PYTHON -m venv venv
else
    echo " [OK] Virtual environment exists"
fi

source venv/bin/activate

# ---- Install PyTorch ----
echo ""
echo " [2/5] Installing PyTorch..."

if command -v nvidia-smi &> /dev/null; then
    echo "        NVIDIA GPU detected - installing CUDA version"
    pip install torch torchaudio --index-url https://download.pytorch.org/whl/cu121 -q
elif [[ "$(uname)" == "Darwin" ]]; then
    echo "        macOS detected - installing default PyTorch"
    pip install torch torchaudio -q
else
    echo "        No GPU detected - installing CPU version"
    pip install torch torchaudio --index-url https://download.pytorch.org/whl/cpu -q
fi

# ---- Install dependencies ----
echo ""
echo " [3/5] Installing dependencies..."
pip install -r requirements.txt -q

# ---- Check FFmpeg ----
echo ""
echo " [4/5] Checking FFmpeg..."
if ! command -v ffmpeg &> /dev/null; then
    echo "        FFmpeg not found - attempting install..."
    if [[ "$(uname)" == "Darwin" ]]; then
        brew install ffmpeg 2>/dev/null || echo "        Install manually: brew install ffmpeg"
    elif command -v apt &> /dev/null; then
        sudo apt install -y ffmpeg 2>/dev/null || echo "        Install manually: sudo apt install ffmpeg"
    else
        echo "        Install FFmpeg manually: https://ffmpeg.org/download.html"
    fi
else
    echo "        [OK] FFmpeg found"
fi

# ---- Download models ----
echo ""
echo " [5/5] Downloading AI models..."
if [ ! -f "OpenVoice/checkpoints_v2/converter/checkpoint.pth" ]; then
    pip install huggingface_hub -q
    python -c "from huggingface_hub import snapshot_download; snapshot_download('myshell-ai/OpenVoiceV2', local_dir='OpenVoice/checkpoints_v2')"
else
    echo "        [OK] Models already downloaded"
fi

# ---- Create directories ----
mkdir -p references output

# ---- Verify ----
echo ""
echo " ===================================================="
echo "     Verifying installation..."
echo " ===================================================="
echo ""

python -c "
import torch
print(f'  PyTorch {torch.__version__} - CUDA: {torch.cuda.is_available()}')
import librosa
print(f'  Librosa {librosa.__version__}')
import sys; sys.path.insert(0, 'OpenVoice')
from openvoice.api import ToneColorConverter
print('  OpenVoice: OK')
"

echo ""
echo " ===================================================="
echo "     Setup complete!"
echo " ===================================================="
echo ""
echo " To use, first activate the environment:"
echo ""
echo "   source venv/bin/activate"
echo ""
echo " Then clone a voice:"
echo ""
echo "   python tools/clone_voice.py -r my_voice.wav -i song.mp3 -o output.wav"
echo ""
echo " Or separate a song first:"
echo ""
echo "   python tools/separate.py -i song.mp3"
echo ""
