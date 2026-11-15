# KID-AI

Key Intelligence Driver (K.I.D) is a local-only AI desktop assistant intended for Linux Mint. It is designed to stay fully offline after setup and to use local inference through Ollama rather than cloud services.

## Current local configuration

This repository now includes a hardware-aware local foundation with the following defaults for the development machine described by the project:

- Primary model: `llama3.2:3b`
- Lightweight model: `llama3.2:1b`
- Vision model: `qwen2.5vl:3b`
- Experimental model: `llama3:8b`
- Ollama endpoint: `http://127.0.0.1:11434`
- No automatic downloads; models must be installed with Ollama separately
- Local-only checks for Ollama, model availability, memory pressure, and hardware status

## Local features

- Hardware and resource inspection
- Local loopback-only Ollama client
- Desktop UI status panel with model and memory warnings
- Memory store using SQLite for preferences, notes, and conversation history
- Offline Vosk adapter configuration and Piper TTS adapter stubs for local speech
- File/tool execution guardrails with explicit permission checks for local-only operations

## Installation

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e '.[test]'
```

Then start the app:

```bash
kid
```

## Environment variables

```bash
export KID_OLLAMA_URL=http://127.0.0.1:11434
export KID_MODEL_PRIMARY=llama3.2:3b
export KID_MODEL_LIGHTWEIGHT=llama3.2:1b
export KID_MODEL_VISION=qwen2.5vl:3b
export KID_MODEL_EXPERIMENTAL=llama3:8b
export KID_VOSK_MODEL_NAME=vosk-model-cn-0.22
export KID_VOSK_MODEL_PATH="$HOME/.local/share/vosk/vosk-model-cn-0.22"
export KID_PIPER_VOICE=en_US-lessac-medium
```

## Notes

The project remains intentionally conservative: users must install Ollama models manually, K.I.D does not download them, and the app avoids cloud provider fallback. Local speech recognition and local speech synthesis are configured as explicit offline components, not cloud alternatives.
