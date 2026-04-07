#!/usr/bin/env bash
set -e

echo "============================================"
echo " Voice Cloner - Setup"
echo "============================================"
echo

# Check Python
if ! command -v python3 &> /dev/null; then
    echo "ERROR: Python 3 not found. Install Python 3.10-3.12."
    exit 1
fi

PYTHON=python3
echo "Found: $($PYTHON --version)"

# Create virtual environment
if [ ! -f "bin/activate" ]; then
    echo
    echo "Creating virtual environment..."
    $PYTHON -m venv .
else
    echo "Virtual environment already exists."
fi

# Activate
source bin/activate

# Detect platform for PyTorch
echo
if command -v nvidia-smi &> /dev/null; then
    echo "NVIDIA GPU detected. Installing PyTorch with CUDA 12.1..."
    pip install torch torchaudio --index-url https://download.pytorch.org/whl/cu121
elif [[ "$(uname)" == "Darwin" ]]; then
    echo "macOS detected. Installing PyTorch..."
    pip install torch torchaudio
else
    echo "No GPU detected. Installing PyTorch (CPU)..."
    pip install torch torchaudio --index-url https://download.pytorch.org/whl/cpu
fi

# Install dependencies
echo
echo "Installing dependencies..."
pip install -r requirements.txt

# Download model checkpoints if missing
if [ ! -f "OpenVoice/checkpoints_v2/converter/checkpoint.pth" ]; then
    echo
    echo "Downloading OpenVoice V2 model checkpoints..."
    pip install huggingface_hub
    python -c "from huggingface_hub import snapshot_download; snapshot_download('myshell-ai/OpenVoiceV2', local_dir='OpenVoice/checkpoints_v2')"
else
    echo "Model checkpoints already present."
fi

# Create directories
mkdir -p references output

# Verify
echo
echo "============================================"
echo " Verifying installation..."
echo "============================================"
python -c "
import torch
print(f'PyTorch {torch.__version__} - CUDA: {torch.cuda.is_available()}')
import librosa
print(f'Librosa {librosa.__version__}')
import sys; sys.path.insert(0, 'OpenVoice')
from openvoice.api import ToneColorConverter
print('OpenVoice: OK')
print()
print('Setup complete!')
"

echo
echo "============================================"
echo " Ready! Try:"
echo "   python tools/clone_voice.py -r reference.wav -i song.mp3 -o output.wav"
echo "============================================"
