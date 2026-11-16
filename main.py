from __future__ import annotations

import argparse
import asyncio

from config import AppConfig
from conversation import ConversationEngine
from terminal_ui import TerminalUI


async def async_main() -> None:
    parser = argparse.ArgumentParser(description="K.I.D - Key Intelligence Driver")
    parser.add_argument("--model", help="Use an already-installed Ollama model")
    parser.add_argument("--no-memory", action="store_true", help="Disable persistent memory")
    parser.add_argument("--no-knowledge", action="store_true", help="Disable local document indexing")
    args = parser.parse_args()
    config = AppConfig.from_env()
    if args.model:
        config.chat_model = args.model
    if args.no_memory:
        config.memory_enabled = False
    if args.no_knowledge:
        config.knowledge_enabled = False
    engine = ConversationEngine(config)
    if engine.knowledge:
        try:
            files = engine.knowledge.index_directory()
            if files:
                print(f"Indexed/updated {len(files)} local document(s).")
        except (OSError, RuntimeError) as exc:
            print(f"Knowledge index unavailable: {exc}")
    if config.warmup_model:
        try:
            models = await engine.ollama.available_models()
            if engine.model in models:
                await engine.ollama.warmup(engine.model)
        except Exception as exc:
            print(f"Model warmup skipped: {exc}")
    await TerminalUI(engine).run()


def main() -> None:
    try:
        asyncio.run(async_main())
    except KeyboardInterrupt:
        print("\nK.I.D offline.")


if __name__ == "__main__":
    main()
