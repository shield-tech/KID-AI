from kid.config import Settings
from kid.hardware import model_warning


def test_model_defaults_match_hardware_configuration():
    settings = Settings.from_env()
    assert settings.primary_model == "llama3.2:3b"
    assert settings.lightweight_model == "llama3.2:1b"
    assert settings.vision_model == "qwen2.5vl:3b"
    assert settings.experimental_model == "llama3:8b"
    assert settings.ollama_url == "http://127.0.0.1:11434"


def test_external_ollama_endpoint_is_rejected(monkeypatch):
    monkeypatch.setenv("KID_OLLAMA_URL", "https://example.com")
    try:
        Settings.from_env()
    except ValueError as exc:
        assert "local Ollama" in str(exc)
    else:
        raise AssertionError("external endpoint was accepted")


def test_memory_warning_for_large_model():
    warning = model_warning("llama3:8b", 2.0, 6.0)
    assert warning is not None
    assert "memory headroom" in warning


def test_memory_warning_is_absent_with_headroom():
    assert model_warning("llama3.2:1b", 6.0, 1.5) is None
