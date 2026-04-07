# Setup Guide

## Automatic Setup (Recommended)

### Windows

```batch
setup.bat
```

### Linux / macOS

```bash
chmod +x setup.sh
./setup.sh
```

The setup script will:
1. Create a Python virtual environment
2. Install PyTorch with CUDA support
3. Install all dependencies
4. Download OpenVoice V2 model checkpoints
5. Verify the installation

---

## Manual Setup

### 1. Prerequisites

- **Python 3.10, 3.11, or 3.12** — [Download](https://www.python.org/downloads/)
- **Git** — [Download](https://git-scm.com/)
- **FFmpeg** — [Download](https://ffmpeg.org/download.html) (add to PATH)
- **NVIDIA GPU + CUDA** (optional but recommended for speed)

Check your setup:

```bash
python --version    # Should be 3.10-3.12
git --version
ffmpeg -version
nvidia-smi          # Shows GPU info (skip if using CPU)
```

### 2. Clone the Repository

```bash
git clone https://github.com/JesperMorais/lagomr-st.git
cd lagomr-st
```

### 3. Create Virtual Environment

```bash
python -m venv .
# or using uv (faster):
# uv venv .
```

Activate it:

```bash
# Windows
Scripts\activate

# Linux/Mac
source bin/activate
```

### 4. Install PyTorch

Pick the right command for your system from [pytorch.org](https://pytorch.org/get-started/locally/).

**Windows/Linux with NVIDIA GPU (CUDA 12.1):**

```bash
pip install torch torchaudio --index-url https://download.pytorch.org/whl/cu121
```

**CPU only:**

```bash
pip install torch torchaudio --index-url https://download.pytorch.org/whl/cpu
```

**macOS (Apple Silicon):**

```bash
pip install torch torchaudio
```

### 5. Install Dependencies

```bash
pip install -r requirements.txt
```

### 6. Download Model Checkpoints

The OpenVoice V2 checkpoints should already be included in `OpenVoice/checkpoints_v2/`. If not, download them:

```bash
# Using huggingface-cli
pip install huggingface_hub
python -c "
from huggingface_hub import snapshot_download
snapshot_download('myshell-ai/OpenVoiceV2', local_dir='OpenVoice/checkpoints_v2')
"
```

### 7. Verify Installation

```bash
python -c "
import torch
print(f'PyTorch: {torch.__version__}')
print(f'CUDA available: {torch.cuda.is_available()}')
if torch.cuda.is_available():
    print(f'GPU: {torch.cuda.get_device_name(0)}')
import librosa
print(f'Librosa: {librosa.__version__}')
from openvoice.api import ToneColorConverter
print('OpenVoice: OK')
print('All good!')
"
```

---

## Troubleshooting

### "No module named openvoice"

The scripts automatically add OpenVoice to the Python path. If running custom code, add this at the top:

```python
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'OpenVoice'))
```

### CUDA out of memory

- Close other GPU applications
- Use `--device cpu` flag (slower but works)
- Reduce audio file length

### Poor voice quality

- Use a cleaner reference clip (less background noise)
- Try different `--tau` values (0.1 to 0.5)
- Use a longer reference clip (10-30 seconds of clear speech)
- Make sure the source vocals are cleanly separated

### Demucs separation is slow

First run downloads the model (~1GB). Subsequent runs are faster. GPU acceleration helps significantly.

### FFmpeg not found

- **Windows:** Download from [ffmpeg.org](https://ffmpeg.org/download.html), extract, add the `bin/` folder to your system PATH
- **Linux:** `sudo apt install ffmpeg`
- **macOS:** `brew install ffmpeg`
