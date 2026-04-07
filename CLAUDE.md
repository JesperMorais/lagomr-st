# lagomrost - Voice Cloner & Song Maker

## What this project does

This is a voice cloning toolkit that lets users:
1. **Clone any voice** from a short audio clip (5-30 seconds)
2. **Make songs** with that cloned voice by converting vocals in existing tracks
3. **Separate audio** into vocals + instrumental using Demucs

The core engine is **OpenVoice V2** by MyShell AI (in `OpenVoice/`), which performs tone color conversion — it extracts a voice "fingerprint" from a reference clip and transfers it onto source audio.

## Project structure

```
├── tools/                          # User-facing CLI scripts
│   ├── clone_voice.py              # Main tool: clone voice + make songs
│   └── separate.py                 # Separate vocals from instrumentals
├── OpenVoice/                      # OpenVoice V2 engine (upstream library)
│   ├── openvoice/                  # Core Python library
│   │   ├── api.py                  # ToneColorConverter, BaseSpeakerTTS
│   │   ├── se_extractor.py         # Speaker embedding extraction
│   │   ├── models.py               # Neural network architecture
│   │   └── ...
│   ├── checkpoints_v2/             # Model weights (NOT in git, downloaded during setup)
│   │   ├── converter/              # Tone color converter model (~126MB)
│   │   │   ├── checkpoint.pth
│   │   │   └── config.json
│   │   └── base_speakers/ses/      # Pre-trained voice embeddings per language
│   └── openvoice_app.py            # Gradio web UI (V1 only, NOT compatible with V2)
├── references/                     # User's voice reference clips go here
├── output/                         # Final output tracks
├── separated/                      # Demucs separation output (auto-created)
├── convert_voice.py                # Original hardcoded script (legacy, kept for reference)
├── setup.bat / setup.sh            # One-click setup scripts
├── requirements.txt                # Python dependencies
├── SETUP.md                        # Detailed installation guide
└── README.md                       # User-facing documentation
```

## How the voice cloning pipeline works

1. **Load ToneColorConverter** from `OpenVoice/checkpoints_v2/converter/`
2. **Extract target voice embedding** — uses Whisper VAD to find speech segments in the reference clip, then extracts a speaker embedding tensor (`se.pth`)
3. **Extract source voice embedding** — same process on the source vocals (can skip VAD for clean vocals)
4. **Convert** — the converter transforms the source audio spectrogram to match the target voice's tone color. Key parameter: `tau` (0.0-1.0) controls how strongly to apply the target voice
5. **Mix** — converted vocals are mixed with the original instrumental, volume-balanced and normalized

## Key technical details

- **Model**: OpenVoice V2 ToneColorConverter (config in `checkpoints_v2/converter/config.json`)
- **Audio processing**: 22050 Hz sample rate internally, librosa for loading/resampling
- **Source separation**: Demucs htdemucs model splits vocals/instrumental
- **Speaker embeddings**: Cached in `processed/` directory to avoid reprocessing
- **GPU**: CUDA strongly recommended (~10x faster than CPU)
- **Python**: 3.10-3.12 required. Virtual environment in `venv/`

## How to run the tools

```bash
# Activate venv first
# Windows: venv\Scripts\activate
# Linux:   source venv/bin/activate

# Full pipeline: song in → voice-cloned song out
python tools/clone_voice.py -r references/voice.wav -i song.mp3 -o "output/My Song.wav"

# Just separate a track
python tools/separate.py -i song.mp3

# Convert pre-separated vocals
python tools/clone_voice.py -r references/voice.wav --vocals separated/htdemucs/song/vocals.wav --instrumental separated/htdemucs/song/no_vocals.wav -o output.wav

# Vocals only (no mixing)
python tools/clone_voice.py -r references/voice.wav --vocals vocals.wav --vocals-only -o converted.wav
```

## Important notes for development

- `OpenVoice/` is upstream code — avoid modifying it directly. Our tools wrap it from `tools/`.
- `checkpoints_v2/` is gitignored (126MB). The setup scripts download it from HuggingFace.
- `OpenVoice/openvoice_app.py` is a **V1 Gradio app** that uses `checkpoints/` (V1 format). It does NOT work with our V2 setup. If building a web UI or voice changer, create a new one using the V2 API.
- The `convert_voice.py` in the root is the original prototype with hardcoded paths. `tools/clone_voice.py` is the proper CLI replacement.
- Audio files (*.wav, *.mp3) are gitignored except in `references/`.

## What's NOT built yet

- **Real-time voice changer** — would need a streaming pipeline (mic input → chunk processing → speaker output). The OpenVoice converter works on full files, not streams. Would need to implement overlapping windowed processing.
- **Web UI for V2** — the existing Gradio app is V1 only. A new one would use `ToneColorConverter` from `openvoice.api` with the V2 checkpoints.
- **Batch processing** — converting multiple songs at once.
- **Voice library** — saving/loading multiple cloned voice profiles.
