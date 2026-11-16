# K.I.D

K.I.D (Key Intelligence Driver) is a local-first terminal assistant for SHIELD Smart Robotics Laboratory. It connects directly to local Ollama and does not download models automatically.

## Run

Python 3.11+ is recommended. Run `./install.sh`, then `./start.sh`. Ollama must be installed and running locally. Install a model yourself with your normal Ollama workflow; K.I.D only discovers models available via `/api/tags`.

Copy `.env.example` to `.env` to configure the local API, SQLite memory, knowledge folder, context, generation limits, speech options, and task storage. Put TXT, Markdown, PDF, and DOCX documents under `knowledge/`; startup indexes supported files. Run `/index` to refresh after adding files.

## Commands

- `/help`
- `/models`, `/model`, `/model MODEL_NAME`
- `/voice on|off|status|volume 0..1|speed 0.5..2|name VOICE`
- `/mute`, `/unmute`, `/stop`
- `/clear` clears conversation history but preserves approved memories
- `/memory [search QUERY|history]`
- `/remember topic | text` saves only explicit user-entered content
- `/edit ID topic | text`, `/forget ID`
- `/index`, `/knowledge [index|search QUERY|status]`, `/vision [status|models]`
- `/tasks [list|add TITLE | NOTES|done ID|remove ID|summary]`
- `/system [all|cpu|ram|disk|temperature|network|processes|uptime]`, `/robotics`, `/status`, `/benchmark`, `/exit`

PDF and document retrieval is local and cites source filenames and page references where available. Vision support is reported honestly and only when a local Ollama vision-capable model is actually installed. Robotics mode remains disconnected by default until an explicit, validated hardware protocol is configured.

## Checks

Run tests with `python -m pytest`. Tests use temporary SQLite databases and mocked Ollama streaming, so they do not require a live model, microphone, or audio hardware. Live Ollama performance, voice output, and hardware integration should be tested on the target machine.
