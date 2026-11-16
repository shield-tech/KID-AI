from __future__ import annotations

import os
import sys


def test_config_defaults() -> None:
    import config
    cfg = config.AppConfig()
    assert cfg.ollama_base_url == "http://127.0.0.1:11434"
    assert cfg.chat_model == "llama3.2"
    assert cfg.default_model == "llama3.2"


def test_security_confirmation_flow() -> None:
    from security import SecurityManager
    sec = SecurityManager(audit_path="test_audit.log")
    assert sec.guard_command("ls /tmp")
    assert not sec.guard_command("sudo rm -rf /")


def test_conversation_commands() -> None:
    from conversation import ConversationEngine
    engine = ConversationEngine(object())
    assert engine.handle_command("/help").startswith("Commands:")
    assert engine.handle_command("/status").startswith("K.I.D is ready")

