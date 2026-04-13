#!/usr/bin/env python3
"""Web UI for voice cloning — launches a localhost Gradio app."""

import sys
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

# Add OpenVoice to path
sys.path.insert(0, str(ROOT / "OpenVoice"))

# Add local venv Scripts to PATH for ffmpeg / demucs
for scripts_dir in [ROOT / "venv" / "Scripts", ROOT / "venv" / "bin", ROOT / "Scripts"]:
    if scripts_dir.exists():
        os.environ["PATH"] = str(scripts_dir) + os.pathsep + os.environ.get("PATH", "")
        break

import torch
import librosa
import soundfile as sf
import numpy as np
import gradio as gr
from openvoice.api import ToneColorConverter
from openvoice import se_extractor

# ---------------------------------------------------------------------------
# Globals (loaded once at startup)
# ---------------------------------------------------------------------------
DEVICE = "cuda:0" if torch.cuda.is_available() else "cpu"
CKPT_DIR = ROOT / "OpenVoice" / "checkpoints_v2" / "converter"
OUTPUT_DIR = ROOT / "output"
SEPARATED_DIR = ROOT / "separated"
REFERENCES_DIR = ROOT / "references"
OUTPUT_DIR.mkdir(exist_ok=True)

converter = None  # lazy-loaded


def load_converter():
    global converter
    if converter is not None:
        return converter
    if not (CKPT_DIR / "checkpoint.pth").exists():
        raise FileNotFoundError(
            "Model checkpoints not found. Run setup.bat / setup.sh first."
        )
    print(f"Loading ToneColorConverter on {DEVICE}...")
    converter = ToneColorConverter(str(CKPT_DIR / "config.json"), device=DEVICE)
    converter.watermark_model = None
    converter.load_ckpt(str(CKPT_DIR / "checkpoint.pth"))
    print("Model loaded.")
    return converter


def separate_audio(input_path: Path):
    """Run demucs to split vocals / instrumental."""
    import subprocess, shutil

    venv_scripts = ROOT / "venv" / ("Scripts" if sys.platform == "win32" else "bin")
    scripts_dir = venv_scripts if venv_scripts.exists() else ROOT / "Scripts"
    demucs_bin = scripts_dir / ("demucs.exe" if sys.platform == "win32" else "demucs")
    if not demucs_bin.exists():
        demucs_bin = shutil.which("demucs")
    if not demucs_bin:
        raise RuntimeError("Demucs not found. Install with: pip install demucs")

    cmd = [str(demucs_bin), "--out", str(SEPARATED_DIR), "--two-stems", "vocals", str(input_path)]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(f"Demucs failed:\n{result.stderr}")

    track_name = input_path.stem
    vocals = SEPARATED_DIR / "htdemucs" / track_name / "vocals.wav"
    instrumental = SEPARATED_DIR / "htdemucs" / track_name / "no_vocals.wav"
    if not vocals.exists() or not instrumental.exists():
        raise RuntimeError(f"Expected output not found in {SEPARATED_DIR / 'htdemucs' / track_name}")
    return vocals, instrumental


# ---------------------------------------------------------------------------
# Main processing function
# ---------------------------------------------------------------------------
def process(reference_audio, input_audio, vocals_audio, instrumental_audio,
            tau, vocal_boost, instrumental_vol, vocals_only, progress=gr.Progress()):
    """Run the full voice cloning pipeline and return the output audio path."""
    try:
        conv = load_converter()

        # --- Determine reference ---
        if reference_audio is None:
            return "Upload a reference voice clip.", None
        ref_path = Path(reference_audio)

        # --- Determine vocals & instrumental ---
        vocals_path = None
        inst_path = None

        if input_audio is not None:
            # Full song provided — run separation
            progress(0.1, desc="Separating vocals...")
            input_path = Path(input_audio)
            vocals_path, inst_path = separate_audio(input_path)
        elif vocals_audio is not None:
            vocals_path = Path(vocals_audio)
            if instrumental_audio is not None:
                inst_path = Path(instrumental_audio)
        else:
            return "Provide either a full song or a vocals file.", None

        # --- Extract embeddings ---
        progress(0.3, desc="Extracting reference voice...")
        target_se, _ = se_extractor.get_se(str(ref_path), conv, target_dir='processed', vad=True)

        progress(0.5, desc="Extracting source voice...")
        source_se = conv.extract_se([str(vocals_path)])

        # --- Convert ---
        progress(0.6, desc="Converting voice...")
        converted_path = str(OUTPUT_DIR / "converted_tmp.wav")
        conv.convert(
            audio_src_path=str(vocals_path),
            src_se=source_se,
            tgt_se=target_se,
            output_path=converted_path,
            tau=tau,
            message="default",
        )

        # --- Mix or return vocals only ---
        final_path = str(OUTPUT_DIR / "web_output.wav")

        if vocals_only or inst_path is None:
            import shutil
            shutil.copy(converted_path, final_path)
            status = "Done — converted vocals only."
        else:
            progress(0.8, desc="Mixing with instrumental...")
            vocals_audio_data, sr_v = librosa.load(converted_path, sr=None)
            instrumental_data, sr_i = librosa.load(str(inst_path), sr=None)

            if sr_v != sr_i:
                instrumental_data = librosa.resample(instrumental_data, orig_sr=sr_i, target_sr=sr_v)

            min_len = min(len(vocals_audio_data), len(instrumental_data))
            vocals_audio_data = vocals_audio_data[:min_len]
            instrumental_data = instrumental_data[:min_len]

            mixed = vocals_audio_data * vocal_boost + instrumental_data * instrumental_vol
            mixed = mixed / np.max(np.abs(mixed)) * 0.95

            sf.write(final_path, mixed, sr_v)
            status = "Done — mixed output ready."

        # Cleanup temp
        if os.path.exists(converted_path) and converted_path != final_path:
            os.remove(converted_path)

        progress(1.0, desc="Complete!")
        return status, final_path

    except Exception as e:
        return f"Error: {e}", None


# ---------------------------------------------------------------------------
# Gradio UI
# ---------------------------------------------------------------------------
def list_references():
    """List existing reference files."""
    if REFERENCES_DIR.exists():
        return sorted([str(p) for p in REFERENCES_DIR.glob("*") if p.suffix.lower() in (".wav", ".mp3", ".flac", ".ogg")])
    return []


def build_ui():
    with gr.Blocks(title="Voice Changer", theme=gr.themes.Soft()) as app:
        gr.Markdown("# Voice Changer\nClone any voice and apply it to a song or vocal track.")

        with gr.Row():
            with gr.Column():
                gr.Markdown("### Reference Voice")
                reference_audio = gr.Audio(
                    label="Upload reference voice (5-30s clip)",
                    type="filepath",
                )
                ref_dropdown = gr.Dropdown(
                    label="Or pick from references/",
                    choices=list_references(),
                    value=None,
                    interactive=True,
                )

                def pick_reference(choice):
                    return choice
                ref_dropdown.change(pick_reference, ref_dropdown, reference_audio)

                gr.Markdown("### Input Audio")
                gr.Markdown("*Option A: Upload a full song (auto-separates vocals)*")
                input_audio = gr.Audio(label="Full song", type="filepath")

                gr.Markdown("*Option B: Upload pre-separated files*")
                vocals_audio = gr.Audio(label="Vocals", type="filepath")
                instrumental_audio = gr.Audio(label="Instrumental (optional)", type="filepath")

            with gr.Column():
                gr.Markdown("### Settings")
                tau = gr.Slider(0.0, 1.0, value=0.3, step=0.05,
                                label="Voice similarity (tau)",
                                info="Higher = more like reference voice")
                vocal_boost = gr.Slider(0.5, 2.0, value=1.2, step=0.1,
                                        label="Vocal volume boost")
                instrumental_vol = gr.Slider(0.0, 2.0, value=0.9, step=0.1,
                                             label="Instrumental volume")
                vocals_only = gr.Checkbox(label="Output vocals only (no mixing)", value=False)

                convert_btn = gr.Button("Convert", variant="primary", size="lg")

                gr.Markdown("### Output")
                status_text = gr.Textbox(label="Status", interactive=False)
                output_audio = gr.Audio(label="Result", type="filepath")

        convert_btn.click(
            process,
            inputs=[reference_audio, input_audio, vocals_audio, instrumental_audio,
                    tau, vocal_boost, instrumental_vol, vocals_only],
            outputs=[status_text, output_audio],
        )

    return app


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--share", action="store_true", help="Create a public Gradio link")
    parser.add_argument("--port", type=int, default=7860, help="Port (default: 7860)")
    args = parser.parse_args()

    app = build_ui()
    app.queue()
    app.launch(server_name="0.0.0.0", server_port=args.port, share=args.share)
