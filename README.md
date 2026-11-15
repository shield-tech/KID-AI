# K.I.D — Key Intelligence Driver

K.I.D is configured as a **local-only** Linux desktop assistant using the Ollama service on loopback. It never uses cloud AI providers and does not automatically download models. Ollama must be installed and running separately.

## Hardware target and defaults

Defaults are intended for the supplied Linux Mint machine (Core i3-8130U, 8 GB RAM, Intel UHD 620):

- Conversation: `llama3.2:3b`
- Lightweight mode / memory-pressure selection: `llama3.2:1b`
- Vision (selected only when explicitly requested by a future vision workflow): `qwen2.5vl:3b`
- Optional experimental: `llama3:8b` (likely to have limited memory headroom on an 8 GB machine)
- Ollama: `http://127.0.0.1:11434`

K.I.D checks locally installed model names and the loaded-model list. It sends inference only to Ollama's loopback API, reports unavailable models, and never invokes the Ollama pull API. RAM estimates are conservative warnings, not guarantees; actual model memory varies with quantization, context size, and runtime overhead.

## Install and run

Python 3.11+ is required. Install Ollama separately and download only the models you want. For example, run `ollama pull llama3.2:3b` manually if you choose to install it; K.I.D itself never downloads models.

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -e '.[test]'
kid
```

Run tests with `pytest`. Model inference requires a running local Ollama service. If Ollama is unavailable, the GUI reports that condition rather than switching providers.

## Configuration

Optional environment variables:

```bash
export KID_OLLAMA_URL=http://127.0.0.1:11434
export KID_MODEL_PRIMARY=llama3.2:3b
export KID_MODEL_LIGHTWEIGHT=llama3.2:1b
export KID_MODEL_VISION=qwen2.5vl:3b
export KID_MODEL_EXPERIMENTAL=llama3:8b
export KID_DATA_DIR="$HOME/.local/share/kid"
```

The endpoint is intentionally restricted to localhost. `KID_MODEL_*` settings change configured model names; models must already be installed in Ollama. Model selection and local hardware status are shown in the desktop window.

## Current scope

This configuration adds local Ollama selection, connection/model status, basic hardware reporting, memory warnings, and a background-thread chat interface. Persistent memory, voice, image upload/vision invocation, streaming generation, and permissioned computer tools are not implemented by this configuration slice; the vision model is listed but not loaded or invoked automatically.
