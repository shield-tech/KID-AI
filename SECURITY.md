# K.I.D Security Model

K.I.D enforces a restricted local execution model.

## Rules

- No external cloud AI providers are configured.
- Only localhost Ollama endpoint is permitted.
- File access is limited to approved local directories.
- Command execution is restricted to an explicit allowlist.
- Sensitive credentials are not stored in the memory database.
- Local actions are logged to the local activity log.

## Users are responsible for installing models manually

K.I.D does not download models automatically. This prevents surprise network activity and keeps the app privacy-first.
