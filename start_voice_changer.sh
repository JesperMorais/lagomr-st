#!/bin/bash
echo "============================================"
echo "  Voice Changer - Starting Web UI..."
echo "============================================"
echo

# Activate virtual environment
if [ -f "venv/bin/activate" ]; then
    source venv/bin/activate
else
    echo "[WARNING] Virtual environment not found. Run setup.sh first."
    exit 1
fi

# Check that gradio is installed
python -c "import gradio" 2>/dev/null
if [ $? -ne 0 ]; then
    echo "Installing Gradio..."
    pip install gradio
fi

# Launch the web UI
echo "Starting on http://localhost:7860"
echo
python tools/voice_changer_app.py "$@"
