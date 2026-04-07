#!/usr/bin/env python3
"""Clone a voice and apply it to a song or vocal track."""

import argparse
import sys
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

# Add OpenVoice to path
sys.path.insert(0, str(ROOT / "OpenVoice"))

# Add local Scripts to PATH for ffmpeg etc.
os.environ["PATH"] = str(ROOT / "Scripts") + os.pathsep + os.environ.get("PATH", "")


def auto_device():
    import torch
    return "cuda:0" if torch.cuda.is_available() else "cpu"


def separate_audio(input_path, output_dir):
    """Run demucs to separate vocals from instrumental."""
    import subprocess

    scripts_dir = ROOT / "Scripts"
    demucs_bin = scripts_dir / ("demucs.exe" if sys.platform == "win32" else "demucs")
    if not demucs_bin.exists():
        import shutil
        demucs_bin = shutil.which("demucs")

    if not demucs_bin:
        print("Error: Demucs not found. Install with: pip install demucs")
        sys.exit(1)

    cmd = [str(demucs_bin), "--out", str(output_dir), "--two-stems", "vocals", str(input_path)]
    print(f"Separating vocals from: {input_path.name}")
    result = subprocess.run(cmd)
    if result.returncode != 0:
        print("Error: Source separation failed.")
        sys.exit(1)

    track_name = input_path.stem
    vocals = output_dir / "htdemucs" / track_name / "vocals.wav"
    instrumental = output_dir / "htdemucs" / track_name / "no_vocals.wav"

    if not vocals.exists() or not instrumental.exists():
        print(f"Error: Expected output files not found in {output_dir / 'htdemucs' / track_name}")
        sys.exit(1)

    return vocals, instrumental


def extract_embedding(converter, audio_path, use_vad=True):
    """Extract speaker embedding from audio."""
    from openvoice import se_extractor

    if use_vad:
        se, _ = se_extractor.get_se(str(audio_path), converter, vad=True)
    else:
        se = converter.extract_se([str(audio_path)])
    return se


def main():
    parser = argparse.ArgumentParser(
        description="Clone a voice and apply it to a song.",
        epilog="Examples:\n"
               "  python clone_voice.py -r voice.wav -i song.mp3 -o output.wav\n"
               "  python clone_voice.py -r voice.wav --vocals vocals.wav --instrumental inst.wav -o output.wav",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--reference", "-r", required=True,
                        help="Reference voice clip to clone (5-30s, WAV or MP3)")
    parser.add_argument("--input", "-i", default=None,
                        help="Full song file (will auto-separate vocals/instrumental)")
    parser.add_argument("--vocals", default=None,
                        help="Pre-separated vocals file")
    parser.add_argument("--instrumental", default=None,
                        help="Pre-separated instrumental file")
    parser.add_argument("--output", "-o", default="output.wav",
                        help="Output file path (default: output.wav)")
    parser.add_argument("--tau", type=float, default=0.3,
                        help="Voice similarity strength 0.0-1.0 (default: 0.3)")
    parser.add_argument("--vocal-boost", type=float, default=1.2,
                        help="Vocal volume multiplier (default: 1.2)")
    parser.add_argument("--instrumental-vol", type=float, default=0.9,
                        help="Instrumental volume multiplier (default: 0.9)")
    parser.add_argument("--device", default=None,
                        help="Device: cuda:0 or cpu (default: auto-detect)")
    parser.add_argument("--vocals-only", action="store_true",
                        help="Output only the converted vocals (no mixing)")
    args = parser.parse_args()

    # Validate inputs
    ref_path = Path(args.reference).resolve()
    if not ref_path.exists():
        print(f"Error: Reference file not found: {ref_path}")
        sys.exit(1)

    if args.input is None and args.vocals is None:
        print("Error: Provide either --input (full song) or --vocals (pre-separated vocals)")
        sys.exit(1)

    device = args.device or auto_device()

    import torch
    import librosa
    import soundfile as sf
    import numpy as np
    from openvoice.api import ToneColorConverter

    print(f"Using device: {device}")

    # Load model
    ckpt_dir = ROOT / "OpenVoice" / "checkpoints_v2" / "converter"
    print("Loading ToneColorConverter...")
    converter = ToneColorConverter(str(ckpt_dir / "config.json"), device=device)
    converter.watermark_model = None
    converter.load_ckpt(str(ckpt_dir / "checkpoint.pth"))

    # Get vocals and instrumental
    if args.input:
        input_path = Path(args.input).resolve()
        if not input_path.exists():
            print(f"Error: Input file not found: {input_path}")
            sys.exit(1)
        separated_dir = ROOT / "separated"
        vocals_path, instrumental_path = separate_audio(input_path, separated_dir)
    else:
        vocals_path = Path(args.vocals).resolve()
        instrumental_path = Path(args.instrumental).resolve() if args.instrumental else None
        if not vocals_path.exists():
            print(f"Error: Vocals file not found: {vocals_path}")
            sys.exit(1)
        if instrumental_path and not instrumental_path.exists():
            print(f"Error: Instrumental file not found: {instrumental_path}")
            sys.exit(1)

    # Extract embeddings
    print("Extracting reference voice embedding...")
    target_se = extract_embedding(converter, ref_path, use_vad=True)
    print(f"  Reference embedding shape: {target_se.shape}")

    print("Extracting source voice embedding...")
    source_se = extract_embedding(converter, vocals_path, use_vad=False)
    print(f"  Source embedding shape: {source_se.shape}")

    # Convert vocals
    converted_path = str(Path(args.output).with_suffix("")) + "_vocals_tmp.wav"
    print(f"Converting vocals (tau={args.tau})...")
    converter.convert(
        audio_src_path=str(vocals_path),
        src_se=source_se,
        tgt_se=target_se,
        output_path=converted_path,
        tau=args.tau,
        message="default",
    )

    output_path = Path(args.output).resolve()
    output_path.parent.mkdir(parents=True, exist_ok=True)

    if args.vocals_only or not instrumental_path:
        # Just output the converted vocals
        import shutil
        shutil.move(converted_path, str(output_path))
        print(f"\nConverted vocals saved to: {output_path}")
    else:
        # Mix with instrumental
        print("Mixing vocals with instrumental...")
        vocals, sr_v = librosa.load(converted_path, sr=None)
        instrumental, sr_i = librosa.load(str(instrumental_path), sr=None)

        if sr_v != sr_i:
            instrumental = librosa.resample(instrumental, orig_sr=sr_i, target_sr=sr_v)

        min_len = min(len(vocals), len(instrumental))
        vocals = vocals[:min_len]
        instrumental = instrumental[:min_len]

        mixed = vocals * args.vocal_boost + instrumental * args.instrumental_vol
        mixed = mixed / np.max(np.abs(mixed)) * 0.95

        sf.write(str(output_path), mixed, sr_v)

        # Clean up temp file
        os.remove(converted_path)

        print(f"\nFinal track saved to: {output_path}")

    print("Done!")


if __name__ == "__main__":
    main()
