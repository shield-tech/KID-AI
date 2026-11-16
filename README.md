# K.I.D

K.I.D (Key Intelligence Driver) is a local-first terminal assistant for SHIELD Smart Robotics Laboratory. It connects directly to local Ollama and does not download models or voice assets automatically.

## Install and start

Python 3.11+ is recommended. Run `./install.sh`, optionally copy `.env.example` to `.env`, then run `./start.sh`. The launcher uses the project virtual environment directly and forwards CLI arguments. Ollama must already be installed and running locally; choose from models reported by `/models`.

## Local voice setup

Piper is preferred. Install Piper using a trusted local package/source, then place the voice `.onnx` and matching `.onnx.json` in `voices/` (or configure `KID_PIPER_VOICE_DIR`). K.I.D will not fetch large voice files. Piper playback uses `paplay` for configured volume when available, otherwise `aplay`; install `espeak-ng` as fallback. Adjust with `/voice volume 0..1`, `/voice speed 0.5..2`, `/voice name NAME`, `/mute`, and `/unmute`.

For offline input, install the optional Vosk and sounddevice dependencies, download a Vosk model yourself into `models/vosk` or set `VOSK_MODEL_DIR`, and explicitly activate push-to-talk. The application does not continuously record audio. Manual text input remains available.

## Commands

- `/help`, `/status`, `/models`, `/model [NAME]`, `/benchmark`
- `/voice [on|off|status|volume N|speed N|name NAME]`, `/mute`, `/unmute`, `/stop`
- `/memory [search QUERY|history]`, `/remember topic | text`, `/edit ID topic | text`, `/forget ID`, `/clear`
- `/knowledge [status|index|search QUERY]`, `/vision [status|models]`
- `/tasks [list|add TITLE | NOTES|done ID|remove ID|summary]`
- `/system [all|cpu|ram|swap|disk|temperature|network|processes|uptime|platform]`, `/robotics`, `/exit`

`/system` reports local read-only telemetry; unavailable sensor/dependency readings are explicitly labeled. `/robotics` reports simulation/hardware mode, serial port state separately from verified device identity, and whether motion is enabled. Opening a serial port alone is not device verification; no generic movement protocol is implemented, and the software E-stop latch is not a safety-rated physical stop.

## Test

Run `python -m pytest`. Tests use temporary data and mocked components; live Ollama, audio hardware, microphones, and physical robot connectivity must be validated on the target machine.
