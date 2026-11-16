from __future__ import annotations

import asyncio
import shutil
from datetime import datetime
from typing import Any


class TerminalUI:
    BLUE = "\033[94m"
    CYAN = "\033[96m"
    GREEN = "\033[92m"
    DIM = "\033[2m"
    RESET = "\033[0m"

    def __init__(self, engine: Any) -> None:
        self.engine = engine
        self._color = bool(getattr(__import__("sys"), "stdout").isatty())

    def _paint(self, text: str, color: str) -> str:
        return f"{color}{text}{self.RESET}" if self._color else text

    async def print_banner(self) -> None:
        ollama_online = await self.engine.ollama.health()
        model_status = "model discovery pending"
        try:
            models = await self.engine.ollama.available_models() if ollama_online else []
            if not self.engine.model and models:
                self.engine.set_model(models[0])
            model_status = f"{self.engine.model} selected" if self.engine.model in models else ("no installed model found" if not models else "selected model not installed")
        except Exception as exc:
            model_status = str(exc)
        speech = shutil.which("piper") or shutil.which("espeak-ng") or shutil.which("espeak")
        docs = len(self.engine.knowledge.indexed_files()) if self.engine.knowledge else 0
        mem = "enabled" if self.engine.memory else "disabled"
        print()
        print(self._paint("K.I.D", self.CYAN))
        print("KEY INTELLIGENCE DRIVER")
        print("SHIELD ADVANCED AI SYSTEM")
        print()
        print(f"[{'ONLINE' if ollama_online else 'OFFLINE'}] Intelligence Engine — {model_status}")
        print(f"[{'ONLINE' if self.engine.memory else 'OFF'}] Memory System — {mem}")
        print(f"[{'ONLINE' if speech else 'OFF'}] Speech Output — {speech or 'Piper/espeak not detected'}")
        print(f"[READY] Knowledge Index — {docs} indexed document(s); /index to refresh")
        print("Type /help for commands. Ollama models are never downloaded automatically.")
        print()

    async def run(self) -> None:
        await self.print_banner()
        while True:
            try:
                prompt = (await asyncio.to_thread(input, self._paint("K.I.D > ", self.GREEN))).strip()
            except (EOFError, KeyboardInterrupt):
                print("\nK.I.D offline.")
                break
            if not prompt:
                continue
            if prompt.startswith("/"):
                response = await self.engine.handle_command(prompt)
                if response == "EXIT":
                    print("K.I.D offline.")
                    break
                print(response)
                continue
            started = datetime.now().astimezone().strftime("%H:%M:%S")
            print(self._paint(f"[{started}] K.I.D: ", self.CYAN), end="", flush=True)
            try:
                async for token in self.engine.stream_response(prompt):
                    print(token, end="", flush=True)
                stats = getattr(self.engine.ollama, "last_stats", {})
                duration = getattr(self.engine, "last_response_seconds", 0.0)
                eval_count = stats.get("eval_count")
                suffix = f" | {eval_count / duration:.1f} tok/s" if eval_count and duration > 0 else ""
                print(self._paint(f"\n{self.DIM}({duration:.2f}s{suffix}){self.RESET}" if self._color else f"\n({duration:.2f}s{suffix})"))
            except asyncio.CancelledError:
                print("\n[Generation stopped]")
            except Exception as exc:
                print(f"\n[Error] {exc}")


__all__ = ["TerminalUI"]
