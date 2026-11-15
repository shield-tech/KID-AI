# K.I.D Troubleshooting

## Ollama not connected

The app reports when the local Ollama service is unavailable. Ensure the service is running:

```bash
ollama serve
```

## Model not found

The installed models list is pulled from the local Ollama API. Install the exact model manually:

```bash
ollama pull llama3.2:3b
```

## Memory warning

Select the lightweight model or reduce the active context. K.I.D warns before using memory-heavy models on smaller machines.
