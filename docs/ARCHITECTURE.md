# Local Ollama Architecture

`kid.config.Settings` owns the loopback-only Ollama endpoint and configurable model names. `kid.ollama.OllamaClient` checks `/api/tags` and `/api/ps` before inference and uses `/api/chat` only for an installed model; no pull endpoint or cloud provider exists. `kid.hardware.inspect_hardware` reads OS, CPU, RAM, DRM GPU identification, and disk information locally. `kid.ui.main_window.MainWindow` presents model selection, system status and a background-thread conversation UI.

Model defaults are profile settings, not repeated constants: `llama3.2:3b` primary, `llama3.2:1b` lightweight, `qwen2.5vl:3b` vision, and `llama3:8b` experimental. The vision model is not requested unless an explicit image workflow is added. This GUI currently exposes configured model names among the locally installed models; it does not support image submission, so it cannot load/use vision yet.

Model RAM figures are rough estimates used only to warn about headroom. Available RAM, quantization, context length, and Ollama overhead affect real usage. The lightweight mode chooses the 1B model. Automatic pressure selection is limited to the UI's current RAM check; it does not kill or unload Ollama models. Ollama reports currently loaded models via `/api/ps`.

No network service other than the exact loopback Ollama endpoint is configured. Model downloads are intentionally a user-managed setup action performed outside K.I.D.
