# KID-AI

Key Intelligence Driver (K.I.D) is a Python-first foundation for an extensible AI assistant that supports multiple language model providers, a provider-neutral orchestration layer, and a clean path to tool- and workflow-based autonomy.

This repository now includes a modular starter implementation with:

- A provider-neutral assistant core
- OpenAI and Google Gemini adapters
- Environment-driven configuration and validation
- Unit tests for assistant behavior and configuration
- A command-line entry point for quick interaction

## Project status

This is an initial, working architecture foundation. It is intentionally small, testable, and extensible. The current release is designed to be safely expanded with tools, memory, telemetry, and future autonomous capabilities without coupling the core assistant to any single provider.

## Python setup

Use Python 3.11 or newer.

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e .
```

## Environment variables

Set the model provider and credentials before running:

```bash
export KID_PROVIDER=openai
export OPENAI_API_KEY="your-openai-key"
export KID_MODEL="gpt-4o-mini"
```

Or use Gemini:

```bash
export KID_PROVIDER=gemini
export GEMINI_API_KEY="your-gemini-key"
export KID_MODEL="gemini-1.5-flash"
```

## Run the assistant

```bash
kid "Summarize the importance of modular AI architecture."
```

You can also invoke the module directly:

```bash
python -m kid.app "Write a short system prompt for a helpful assistant."
```

## Development

```bash
python -m pip install -e ".[dev]"
pytest
```

## Architecture goals

- Provider-neutral orchestration in `kid.core`
- Provider-specific adapters isolated in `kid.providers`
- Strong validation and explicit configuration errors
- Simple, maintainable interfaces
- Safe future extension to tools, memory, and workflow control

## Repository structure

```text
src/kid/
  app.py
  config.py
  core/
    assistant.py
    errors.py
    models.py
  providers/
    __init__.py
    base.py
    factory.py
    gemini.py
    openai.py

docs/
  ARCHITECTURE.md

tests/
  unit/
    test_assistant.py
    test_config.py
    test_factory.py
```

## License

This project is in its early development stage and does not yet define a production license.
