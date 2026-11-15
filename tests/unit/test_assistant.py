# K.I.D Architecture

## 1. Goals

K.I.D is intended to become a modular AI assistant platform capable of:

- multi-provider model access (OpenAI, Gemini, and future providers)
- human-friendly conversation and tool usage
- explicit security boundaries for sensitive operations
- clean separation between orchestration and provider implementation
- operational observability and safe error handling

## 2. Architectural principles

1. Core logic must not depend on third-party SDK implementation details.
2. Providers are isolated adapters behind a stable interface.
3. Configuration is explicit, validated, and environment-driven.
4. State and tool access remain separate concerns from model orchestration.
5. New capabilities are added by composition, not by modifying core logic for each feature.

## 3. Package layout

```text
src/kid/
  app.py                  CLI entry point
  config.py               env/setting parsing and validation
  __init__.py             package metadata
  core/
    assistant.py          orchestration and conversation flow
    errors.py             shared exceptions
    models.py             common request/response types
  providers/
    base.py               provider interface contract
    factory.py            provider selection logic
    openai.py             OpenAI adapter
    gemini.py             Gemini adapter
```

## 4. Core responsibilities

### `kid.core.assistant.KIDAssistant`

- Accepts a provider instance
- Builds provider-neutral message sequences
- Calls provider.generate(...)
- Validates the response object before returning it

### `kid.core.models`

Contains the common data structures used across providers so the orchestration layer can remain stable even as providers change.

### `kid.core.errors`

Keeps error semantics consistent and easy to handle. This prevents the assistant from leaking raw SDK exceptions into the rest of the application.

## 5. Provider adapters

Each provider adapter is responsible for:

- loading its SDK lazily
- validating the API key
- mapping K.I.D message structures to provider-specific payloads
- translating provider responses back to `ProviderResponse`
- converting SDK issues into shared `ProviderError` exceptions

This keeps the assistant portable and allows future providers (Anthropic, local models, etc.) to be added without touching the orchestration layer.

## 6. Configuration strategy

All runtime configuration is environment-driven:

- `KID_PROVIDER`
- `KID_MODEL`
- `OPENAI_API_KEY`
- `GEMINI_API_KEY`
- `KID_TEMPERATURE`
- `KID_MAX_TOKENS`
- `KID_DEBUG`

This allows local development and deployment with explicit secrets management and no hard-coded credentials.

## 7. Testing strategy

The initial test suite is intentionally small and deterministic:

- configuration validation tests
- assistant orchestration tests with a fake provider
- provider factory tests for selection logic
- integration tests remain optional and opt-in, never part of the default security-sensitive workflow

## 8. Future roadmap

Planned extensions include:

- tool execution layer with explicit permission checks
- memory and conversation state management
- structured logging / service telemetry
- workflow automation components
- human approval checkpoints for irreversible actions

The key design decision is to keep tool execution and AI orchestration in distinct layers until there is a clear use case for autonomous action.
