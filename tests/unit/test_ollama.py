from kid.config import Settings
from kid.ollama import OllamaClient, OllamaError, OllamaStatus


def test_external_endpoint_is_rejected():
    settings = Settings(ollama_url="https://example.com")
    try:
        OllamaClient(settings)
    except ValueError:
        pass
    else:
        raise AssertionError("external endpoint was accepted")


def test_status_reports_unavailable_without_cloud_fallback(monkeypatch):
    client = OllamaClient(Settings())

    def fail(_path):
        raise OllamaError("offline")

    monkeypatch.setattr(client, "_get_json", fail)
    status = client.status()
    assert not status.connected
    assert status.error == "offline"


def test_no_installed_model_does_not_infer(monkeypatch):
    client = OllamaClient(Settings())
    monkeypatch.setattr(client, "status", lambda: OllamaStatus(True, ()))
    try:
        client.generate("llama3.2:3b", "hello")
    except OllamaError as exc:
        assert "will not download" in str(exc)
    else:
        raise AssertionError("missing model should fail")
