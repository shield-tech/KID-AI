# K.I.D

K.I.D (Key Intelligence Driver) is a local-first terminal assistant for SHIELD Smart Robotics Laboratory. It connects directly to local Ollama and does not download models automatically.

## Run

Python 3.11+ is recommended. Run `./install.sh`, then `./start.sh`. Ollama must be installed and running locally. Install a model yourself with your normal Ollama workflow; K.I.D only discovers models available via `/api/tags`.

Copy `.env.example` to `.env` to configure the local API, SQLite memory, knowledge folder, context, generation limits, and speech options. Put TXT, Markdown, PDF, and DOCX documents under `knowledge/`; startup indexes supported files. Run `/index` to refresh after adding files.

## Commands

- `/help`
- `/models`, `/model`, `/model MODEL_NAME`
- `/voice on|off`, `/mute`, `/unmute`, `/stop`
- `/clear` clears conversation history but preserves approved memories
- `/memory [search]`
- `/remember topic | text` saves only explicit user-entered content
- `/edit ID topic | text`, `/forget ID`
- `/index`, `/status`, `/benchmark`, `/exit`

PDF page references are retained in retrieval results. Keyword retrieval is local and cites source filenames; it does not claim semantic search. Speech availability is reported based on installed local executables.

## Checks

Run tests with `python -m pytest`. Tests use temporary SQLite databases and mocked Ollama streaming, so they do not require a live model, microphone, or audio hardware. Live Ollama performance and audio behavior must be tested on the target machine.
