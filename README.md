# Voice Cloner & Song Maker

Clone any voice and use it to create songs or build a real-time voice changer. Powered by [OpenVoice V2](https://github.com/myshell-ai/OpenVoice).

## What It Does

- **Clone a voice** from a short audio clip (5-30 seconds)
- **Convert vocals** in any song to sound like the cloned voice
- **Separate vocals** from instrumentals automatically (Demucs)
- **Mix final tracks** with balanced vocals + instrumental
- **Real-time voice changer** (coming soon)

## Quick Start

```bash
# 1. Clone the repo
git clone https://github.com/JesperMorais/lagomr-st.git
cd lagomr-st

# 2. Run setup (creates venv, installs deps, downloads models)
# Windows
setup.bat

# Linux/Mac
chmod +x setup.sh && ./setup.sh

# 3. Clone a voice and convert a song
python tools/clone_voice.py --reference my_voice.wav --input song.mp3 --output my_song.wav
```

See [SETUP.md](SETUP.md) for detailed installation instructions.

## Usage

### Step 1: Separate Vocals from a Song

Split any song into vocals and instrumental tracks:

```bash
python tools/separate.py --input song.mp3
# Output: separated/htdemucs/song/vocals.wav
# Output: separated/htdemucs/song/no_vocals.wav
```

### Step 2: Clone a Voice onto the Vocals

Take a reference voice clip and apply it to the separated vocals:

```bash
python tools/clone_voice.py \
  --reference my_voice.wav \
  --vocals separated/htdemucs/song/vocals.wav \
  --instrumental separated/htdemucs/song/no_vocals.wav \
  --output "My Name - Song Title.wav"
```

### All-in-One (Song In, Voice-Cloned Song Out)

Skip the manual separation step — just provide the full song:

```bash
python tools/clone_voice.py \
  --reference my_voice.wav \
  --input song.mp3 \
  --output "My Name - Song Title.wav"
```

### Options

| Flag | Description | Default |
|------|-------------|---------|
| `--reference` | Voice clip to clone (5-30s WAV/MP3) | *required* |
| `--input` | Full song (auto-separates vocals) | - |
| `--vocals` | Pre-separated vocals file | - |
| `--instrumental` | Pre-separated instrumental file | - |
| `--output` | Output file path | `output.wav` |
| `--tau` | Voice similarity strength (0.0-1.0) | `0.3` |
| `--vocal-boost` | Vocal volume multiplier | `1.2` |
| `--instrumental-vol` | Instrumental volume multiplier | `0.9` |
| `--device` | `cuda:0` or `cpu` | auto-detect |

## Project Structure

```
voice-cloner/
├── tools/
│   ├── clone_voice.py      # Main voice cloning CLI
│   └── separate.py         # Audio source separation CLI
├── OpenVoice/              # OpenVoice V2 engine
│   ├── checkpoints_v2/     # Model weights (downloaded during setup)
│   └── openvoice/          # Core library
├── references/             # Your voice reference clips go here
├── separated/              # Auto-separated vocal/instrumental tracks
├── output/                 # Final output tracks
├── requirements.txt        # Python dependencies
├── setup.bat               # Windows setup script
├── setup.sh                # Linux/Mac setup script
├── SETUP.md                # Detailed setup guide
└── README.md               # This file
```

## How It Works

1. **Voice Embedding Extraction** — Analyzes your reference clip to extract a "tone color" fingerprint of the voice
2. **Source Separation** — Uses [Demucs](https://github.com/facebookresearch/demucs) to split the song into vocals + instrumental
3. **Tone Color Conversion** — OpenVoice V2 transfers the reference voice's characteristics onto the source vocals
4. **Audio Mixing** — Recombines the converted vocals with the original instrumental, normalized and balanced

## Requirements

- Python 3.10-3.12
- NVIDIA GPU with CUDA (recommended) or CPU (slower)
- ~4GB disk space (models + dependencies)
- FFmpeg (included in setup or install separately)

## Tips

- **Better reference clips** = better results. Use clean audio, minimal background noise, 10-30 seconds
- **Lower tau** (0.1-0.3) = more natural but less similar. **Higher tau** (0.5-0.8) = more similar but can sound robotic
- Songs with **clear vocals** convert better than heavily layered or autotuned tracks
- GPU inference is ~10x faster than CPU

## Credits

- [OpenVoice V2](https://github.com/myshell-ai/OpenVoice) by MyShell AI — MIT License
- [Demucs](https://github.com/facebookresearch/demucs) by Meta Research
- [Faster Whisper](https://github.com/SYSTRAN/faster-whisper) for voice activity detection

## License

MIT
