# K.I.D
# Key Intelligence Driver
# SHIELD Advanced AI System

K.I.D is a local-first terminal assistant for SHIELD Smart Robotics Laboratory.

## Overview

K.I.D connects to the local Ollama API, supports memory, local knowledge retrieval, optional voice output, optional voice input, Linux telemetry, and robotics-safe disconnected mode.

## Quick start

1. Install system dependencies if needed:
   - Python 3.11+
   - Ollama
   - Optional: Piper, espeak-ng, Vosk models, microphone hardware
2. Create a virtual environment and install Python dependencies:

```bash
./install.sh
```

3. Start the assistant:

```bash
./start.sh
```

## Environment variables

Copy `.env.example` to `.env` and customize:

```bash
cp .env.example .env
```

## Commands

- `/help`
- `/model`
- `/models`
- `/voice on`
- `/voice off`
- `/mute`
- `/unmute`
- `/stop`
- `/clear`
- `/memory`
- `/remember`
- `/forget`
- `/status`
- `/benchmark`
- `/exit`

## Notes

- The assistant connects to `http://127.0.0.1:11434` by default.
- It discovers available Ollama models dynamically and changes models without a restart when supported.
- Memory is stored in SQLite, not in the model's primary prompt.
- Local documents under `knowledge/` can be searched for context.
- Robotics support is modular and defaults to simulation/disconnected mode until explicitly authorized.

## Troubleshooting

- If Ollama is unavailable, ensure it is running locally on port 11434.
- If audio does not work, install Piper or espeak-ng and ensure the selected voice model exists.
- If Vosk fails, download a model and set the `VOSK_MODEL_DIR` environment variable.
- If a command is unsafe, K.I.D requires explicit confirmation.

## Security

- No secrets are stored in source files.
- Sensitive operations require confirmation.
- External network exposure is disabled by default.
- All local operations remain on the machine.
