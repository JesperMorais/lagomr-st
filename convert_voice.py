import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'OpenVoice'))
os.environ['PATH'] = os.path.join(os.path.dirname(__file__), 'Scripts') + os.pathsep + os.environ.get('PATH', '')

import torch
import librosa
import soundfile as sf
import numpy as np
from openvoice.api import ToneColorConverter
from openvoice import se_extractor

device = "cuda:0" if torch.cuda.is_available() else "cpu"
print(f"Using device: {device}")

# Paths
ckpt_converter = 'C:/Projects/winston_rvc/OpenVoice/checkpoints_v2/converter'
vocals_path = 'C:/Projects/winston_rvc/separated/htdemucs/Smoke_In_The_Warehouse/vocals.wav'
instrumental_path = 'C:/Projects/winston_rvc/separated/htdemucs/Smoke_In_The_Warehouse/no_vocals.wav'
winston_ref = 'C:/Projects/winston_rvc/winston_ref.wav'
output_vocals = 'C:/Projects/winston_rvc/winston_vocals.wav'
output_final = 'C:/Projects/winston_rvc/Winston - Smoke In The Warehouse.wav'

# 1. Load tone color converter
print("Loading ToneColorConverter...")
tone_color_converter = ToneColorConverter(
    f'{ckpt_converter}/config.json', device=device
)
tone_color_converter.watermark_model = None
tone_color_converter.load_ckpt(f'{ckpt_converter}/checkpoint.pth')

# 2. Extract Winston's tone color from reference audio
print("Extracting Winston's voice embedding...")
target_se, audio_name = se_extractor.get_se(
    winston_ref, tone_color_converter, vad=True
)
print(f"Winston SE shape: {target_se.shape}")

# 3. Extract source speaker embedding directly (skip whisper/VAD)
print("Extracting source voice embedding from Suno vocals (direct)...")
source_se = tone_color_converter.extract_se([vocals_path])
print(f"Source SE shape: {source_se.shape}")

# 4. Convert vocals to Winston's voice
print("Converting vocals to Winston's voice...")
tone_color_converter.convert(
    audio_src_path=vocals_path,
    src_se=source_se,
    tgt_se=target_se,
    output_path=output_vocals,
    tau=0.3,
    message="default"
)
print(f"Converted vocals saved to: {output_vocals}")

# 5. Mix converted vocals with instrumental
print("Mixing converted vocals with instrumental...")
vocals, sr_v = librosa.load(output_vocals, sr=None)
instrumental, sr_i = librosa.load(instrumental_path, sr=None)

# Resample if needed
if sr_v != sr_i:
    instrumental = librosa.resample(instrumental, orig_sr=sr_i, target_sr=sr_v)
    sr_i = sr_v

# Match lengths
min_len = min(len(vocals), len(instrumental))
vocals = vocals[:min_len]
instrumental = instrumental[:min_len]

# Mix (boost vocals slightly)
mixed = vocals * 1.2 + instrumental * 0.9

# Normalize
mixed = mixed / np.max(np.abs(mixed)) * 0.95

sf.write(output_final, mixed, sr_v)
print(f"\nFinal track saved to: {output_final}")
print("Done!")
