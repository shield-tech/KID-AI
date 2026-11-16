from __future__ import annotations

import argparse
import asyncio
import os
from typing import List

from config import AppConfig
from conversation import ConversationEngine
from terminal_ui import TerminalUI


async def async_main() -> None:
    parser = argparse.ArgumentParser(description="K.I.D - Key Intelligence Driver")
    parser.add_argument("--voice", action="store_true", help="Enable voice output")
    parser.add_argument("--voice-input", action="store_true", help="Enable voice input")
    parser.add_argument("--model", help="Override chat model")
    parser.add_argument("--no-memory", action="store_true", help="Disable memory")
    parser.add_argument("--no-knowledge", action="store_true", help="Disable local knowledge")
    args = parser.parse_args()

    config = AppConfig.from_env()
    if args.model:
        config.chat_model = args.model
    if args.voice:
        config.voice_output_enabled = True
    if args.voice_input:
        config.voice_input_enabled = True
    if args.no_memory:
        config.memory_enabled = False
    if args.no_knowledge:
        config.knowledge_enabled = False

    engine = ConversationEngine(config)
    ui = TerminalUI(engine)
    await ui.run()


def main() -> None:
    asyncio.run(async_main())


if __name__ == "__main__":
    main()
