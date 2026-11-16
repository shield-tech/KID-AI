from __future__ import annotations

import asyncio
import sys
from datetime import datetime
from typing import Any


class TerminalUI:
    CYAN = "\033[96m"
    GREEN = "\033[92m"
    DIM = "\033[2m"
    RESET = "\033[0m"

    def __init__(self, engine: Any) -> None:
        self.engine = engine
        self._color = bool(sys.stdout.isatty())

    def _paint(self, text: str, color: str) -> str:
        return f"{color}{text}{self.RESET}" if self._color else text

    async def print_banner(self) -> None:
        try:
            ollama_online = await self.engine.ollama.health()
        except Exception:
            ollama_online = False
        try:
            models = await self.engine.ollama.available_models() if ollama_online else []
            if not self.engine.model and models:
                self.engine.set_model(models[0])
            model_status = f"{self.engine.model} selected" if self.engine.model in models else ("no installed models found" if not models else "selected model not verified")
        except Exception:
            models, model_status = [], "model discovery failed"
        memory_ok = self.engine.memory is not None
        try:
            memory_ok = memory_ok and bool(self.engine.memory.db_path)
        except Exception:
            pass
        voice_engine = self.engine.voice.available_engine
        voice_status = "READY" if voice_engine and self.engine.voice_enabled else "DISABLED" if not self.engine.voice_enabled else "UNAVAILABLE"
        docs = len(self.engine.knowledge.indexed_files()) if self.engine.knowledge else 0
        robot = self.engine.robotics.status()
        task_summary = self.engine.tasks.summary()
        print()
        print(self._paint("K.I.D", self.CYAN))
        print("KEY INTELLIGENCE DRIVER")
        print("SHIELD ADVANCED AI SYSTEM")
        print()
        print(f"[{'ONLINE' if ollama_online and models else 'OFFLINE'}] Intelligence Engine — {model_status}")
        print(f"[{'ONLINE' if memory_ok else 'OFFLINE'}] Memory System — {'SQLite active' if memory_ok else 'disabled'}")
        print(f"[{voice_status}] Voice Output — {voice_engine or 'Piper/espeak not detected'}")
        print(f"[READY] Knowledge — {docs} indexed document(s); root: {getattr(self.engine.config, 'knowledge_root', 'disabled')}")
        print(f"[INFO] Tasks — {task_summary['open']} open / {task_summary['completed']} complete")
        print(f"[INFO] Robotics — {robot['mode']} mode; device verified: {'yes' if robot['device_verified'] else 'no'}; motion enabled: no")
        print("Models and voice assets are never downloaded automatically. Type /help for commands.")
        print()

    async def _respond(self, prompt: str) -> None:
        timestamp = datetime.now().astimezone().strftime("%H:%M:%S")
        print(self._paint(f"[{timestamp}] K.I.D: ", self.CYAN), end="", flush=True)
        try:
            async for token in self.engine.stream_response(prompt):
                print(token, end="", flush=True)
            stats = getattr(self.engine.ollama, "last_stats", {})
            duration = getattr(self.engine, "last_response_seconds", 0.0)
            count = stats.get("eval_count")
            rate = count / duration if count and duration > 0 else None
            detail = f"{duration:.2f}s" + (f", {rate:.1f} tok/s" if rate else "")
            print(self._paint(f"\n({detail})", self.DIM))
        except asyncio.CancelledError:
            print("\n[Generation stopped]")
        except Exception as exc:
            print(f"\n[Error] {exc}")

    async def run(self) -> None:
        await self.print_banner()
        try:
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
                    if prompt.split(maxsplit=1)[0].lower() == "/listen" and response.startswith("Recognized: "):
                        transcript = response[len("Recognized: "):].splitlines()[0].strip()
                        if transcript:
                            print(f"Voice input: {transcript}")
                            await self._respond(transcript)
                        else:
                            print("No speech was recognized. You can continue by typing.")
                    else:
                        print(response)
                    continue
                await self._respond(prompt)
        finally:
            self.engine.shutdown()


__all__ = ["TerminalUI"]
