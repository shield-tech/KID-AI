# K.I.D Installation Guide

This guide covers the Linux Mint local-only installation path for K.I.D.

## Prerequisites

- Linux Mint
- Python 3.11+
- Ollama installed locally
- Models installed via Ollama manually, e.g.:

```bash
ollama pull llama3.2:3b
ollama pull llama3.2:1b
ollama pull qwen2.5vl:3b
```

## Create the environment

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e '.[test]'
```

## Start K.I.D

```bash
kid
```

## Troubleshooting

- If Ollama is not running, start it with `ollama serve`.
- If a model is missing, install it manually before using K.I.D.
- If `PySide6` is missing, reinstall with `python -m pip install PySide6`.
- If model warnings appear, switch to lightweight mode or lower the selected model.
