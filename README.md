# KID-AI

Key Intelligence Driver (K.I.D) is a local-only AI desktop assistant built for Linux Mint and intended to remain offline after setup. It uses the local Ollama runtime and does not silently switch to cloud providers.

## What is included

- Local-only Ollama configuration with the required model defaults
- Hardware diagnostics for CPU, RAM, GPU, and free disk space
- SQLite-backed local memory store for notes and conversation history
- Local security and tool guardrails for approved file and command operations
- Vosk configuration for offline speech recognition
- Piper TTS adapter configuration for offline speech synthesis
- PySide6 desktop status UI with local model selection and warnings

## Default model set

- Primary conversation: `llama3.2:3b`
- Lightweight fallback: `llama3.2:1b`
- Vision: `qwen2.5vl:3b`
- Experimental profile: `llama3:8b`
- Not used by default: `llava:latest`

## Local-only constraints

- K.I.D is required to use the local Ollama endpoint only: `http://127.0.0.1:11434`
- No OpenAI, Google Gemini, or other cloud AI provider is configured
- No model downloads occur automatically from K.I.D itself
- The user must install required local models with Ollama before inference

## Install

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e '.[test]'
```

## Run

```bash
kid
```

## Environment overrides

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

## Documentation

The project includes architecture and local operations notes, plus a diagnostics helper for runtime health checks.
