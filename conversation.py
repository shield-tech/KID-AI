from __future__ import annotations

import re
from typing import Any, Dict, List


class ConversationEngine:
    def __init__(self, config: Any) -> None:
        self.config = config
        self.memory = None
        self.knowledge = None
        self.model = None

    def set_memory(self, memory_store: Any) -> None:
        self.memory = memory_store

    def set_knowledge(self, knowledge_base: Any) -> None:
        self.knowledge = knowledge_base

    def set_model(self, model_name: str) -> None:
        self.model = model_name

    def build_system_prompt(self) -> str:
        return (
            "You are K.I.D, Key Intelligence Driver, a calm, concise local AI assistant for SHIELD Smart Robotics Laboratory. "
            "Be professional, helpful, and operationally safe. Never claim to be JARVIS."
        )

    def evaluate_user_command(self, text: str) -> str:
        command = text.strip()
        if not command:
            return "Please provide an instruction."
        if command.startswith("/"):
            return self.handle_command(command)
        return command

    def handle_command(self, command: str) -> str:
        lower = command.lower()
        if lower in {"/help", "/h"}:
            return "Commands: /help /model /models /voice on /voice off /mute /unmute /stop /clear /memory /remember /forget /status /benchmark /exit"
        if lower == "/status":
            return "K.I.D is ready. Local AI mode is enabled. Memory and knowledge are available when configured."
        if lower == "/model":
            return "No model selected yet; the default Ollama model can be changed at runtime."
        if lower == "/models":
            return "Use the Ollama engine to discover available local models."
        if lower in {"/voice on", "/voiceon"}:
            return "Voice output enabled."
        if lower in {"/voice off", "/voiceoff"}:
            return "Voice output disabled."
        if lower == "/mute":
            return "Speech muted."
        if lower == "/unmute":
            return "Speech unmuted."
        if lower == "/clear":
            return "Conversation cleared in memory if available."
        if lower == "/memory":
            return "Memory is persisted in SQLite when enabled."
        if lower == "/remember":
            return "Use the memory tool to save a user-approved fact."
        if lower == "/forget":
            return "Use the memory tool to delete a stored fact."
        if lower == "/benchmark":
            return "Benchmark runner is available in the project."
        if lower == "/exit":
            return "EXIT"
        return "Unknown command. Type /help for command list."


__all__ = ["ConversationEngine"]
