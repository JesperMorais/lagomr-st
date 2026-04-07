#!/usr/bin/env python3
"""Separate a song into vocals and instrumental tracks using Demucs."""

import argparse
import subprocess
import sys
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SCRIPTS_DIR = ROOT / "Scripts"


def find_demucs():
    """Find the demucs executable."""
    # Check local Scripts/ first
    local = SCRIPTS_DIR / "demucs.exe" if sys.platform == "win32" else SCRIPTS_DIR / "demucs"
    if local.exists():
        return str(local)
    # Fall back to PATH
    import shutil
    found = shutil.which("demucs")
    if found:
        return found
    return None


def main():
    parser = argparse.ArgumentParser(
        description="Separate a song into vocals and instrumental tracks."
    )
    parser.add_argument("--input", "-i", required=True, help="Input audio file (MP3, WAV, etc.)")
    parser.add_argument("--output-dir", "-o", default=str(ROOT / "separated"),
                        help="Output directory (default: separated/)")
    parser.add_argument("--model", "-m", default="htdemucs",
                        help="Demucs model to use (default: htdemucs)")
    parser.add_argument("--two-stems", action="store_true", default=True,
                        help="Only separate vocals and accompaniment (default: True)")
    parser.add_argument("--device", "-d", default=None,
                        help="Device: cuda:0 or cpu (default: auto-detect)")
    args = parser.parse_args()

    input_path = Path(args.input).resolve()
    if not input_path.exists():
        print(f"Error: Input file not found: {input_path}")
        sys.exit(1)

    demucs_bin = find_demucs()
    if not demucs_bin:
        print("Error: Demucs not found. Install it with: pip install demucs")
        sys.exit(1)

    cmd = [
        demucs_bin,
        "--out", args.output_dir,
        "-n", args.model,
    ]

    if args.two_stems:
        cmd.extend(["--two-stems", "vocals"])

    if args.device:
        cmd.extend(["-d", args.device])

    cmd.append(str(input_path))

    print(f"Separating: {input_path.name}")
    print(f"Model: {args.model}")
    print(f"Output: {args.output_dir}")
    print()

    result = subprocess.run(cmd)

    if result.returncode == 0:
        track_name = input_path.stem
        output_base = Path(args.output_dir) / args.model / track_name
        print(f"\nDone! Output files:")
        print(f"  Vocals:       {output_base / 'vocals.wav'}")
        print(f"  Instrumental: {output_base / 'no_vocals.wav'}")
    else:
        print(f"\nError: Demucs exited with code {result.returncode}")
        sys.exit(result.returncode)


if __name__ == "__main__":
    main()
