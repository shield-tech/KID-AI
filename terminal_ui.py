from __future__ import annotations

import os
import sys
from typing import Any, Optional


class TerminalUI:
    def __init__(self, engine: Any) -> None:
        self.engine = engine

    def print_banner(self) -> None:
        print("")
        print("K.I.D")
        print("KEY INTELLIGENCE DRIVER")
        print("SHIELD ADVANCED AI SYSTEM")
        print("")
        print("[ONLINE] Intelligence Engine")
        print("[ONLINE] Memory System")
        print("[ONLINE] Speech Output")
        print("[READY] Awaiting Instructions")
        print("")

    async def run(self) -> None:
        self.print_banner()
        while True:
            try:
                prompt = input("K.I.D > ").strip()
            except EOFError:
                print("\nGoodbye.")
                break
            if not prompt:
                continue
            if prompt.lower() in {"exit", "/exit", "quit"}:
                print("K.I.D offline.")
                break
            response = self.engine.evaluate_user_command(prompt)
            if response == "EXIT":
                print("K.I.D offline.")
                break
            print(response)


__all__ = ["TerminalUI"]
