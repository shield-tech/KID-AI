# K.I.D Architecture

## Local-first runtime

K.I.D is structured to remain fully local during operation. The allowed runtime path is loopback-only Ollama (`http://127.0.0.1:11434`), with no cloud inference support. The project explicitly rejects silent fallback to external providers.

## Components

- `kid.config`: local configuration, model profiles, and environment validation
- `kid.hardware`: CPU/RAM/GPU/disk inspection for compatibility warnings
- `kid.ollama`: strict local Ollama client with `/api/tags`, `/api/ps`, and `/api/chat`
- `kid.memory`: SQLite-backed local persistence for notes, preferences, and conversations
- `kid.voice`: local Vosk recognition model configuration and recognition wrapper
- `kid.tts`: local Piper TTS adapter for off-device speech synthesis
- `kid.security`: local tool permission model and command validation layer
- `kid.ui.main_window`: desktop status and chat window using PySide6

## Safety model

The app uses a minimal allowlist for local file and command operations. No shell execution is permitted without explicit policy approval. User-approved actions are logged and can be audited locally. Sensitive credentials are never stored in conversation memory.

## Model policy

Model defaults are intentionally lightweight and hardware-aware:

- `llama3.2:3b` for standard local conversation
- `llama3.2:1b` for lightweight mode and memory pressure
- `qwen2.5vl:3b` for vision capabilities when explicitly requested
- `llama3:8b` as an optional experimental profile only

The project prefers resource-safe behavior over automatic model loading, and it treats local model installation as an explicit user step.
