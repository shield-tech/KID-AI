import pytest

from kid.config import load_settings
from kid.core.errors import ConfigurationError


def test_load_settings_with_openai_defaults(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    monkeypatch.delenv("KID_PROVIDER", raising=False)
    monkeypatch.delenv("KID_MODEL", raising=False)

    settings = load_settings()

    assert settings.provider == "openai"
    assert settings.model == "gpt-4o-mini"
    assert settings.api_key == "test-key"


def test_load_settings_requires_provider_key(monkeypatch):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.setenv("KID_PROVIDER", "openai")

    with pytest.raises(ConfigurationError):
        load_settings()


def test_load_settings_accepts_overrides(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    settings = load_settings(provider="openai", model="gpt-4o-mini", system_prompt="Be brief")

    assert settings.provider == "openai"
    assert settings.model == "gpt-4o-mini"
    assert settings.system_prompt == "Be brief"
