from __future__ import annotations

import argparse
import asyncio
from typing import Sequence

from kid.config import Settings, load_settings
from kid.core.assistant import KIDAssistant
from kid.providers.factory import create_provider


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run the K.I.D assistant")
    parser.add_argument("prompt", nargs="?", help="Prompt to send to the assistant")
    parser.add_argument("--provider", choices=["openai", "gemini"], help="Override the provider")
    parser.add_argument("--model", help="Override the model selection")
    parser.add_argument("--system-prompt", help="Override the default system prompt")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    try:
        settings = load_settings(
            provider=args.provider,
            model=args.model,
            system_prompt=args.system_prompt,
        )
        provider = create_provider(settings)
        assistant = KIDAssistant(provider, system_prompt=settings.system_prompt)

        if args.prompt:
            response = asyncio.run(assistant.chat(args.prompt))
            print(response.text)
        else:
            print("K.I.D ready. Type 'exit' to quit.")
            while True:
                try:
                    raw = input("You> ")
                except EOFError:
                    print()
                    break

                if raw.strip().lower() in {"exit", "quit"}:
                    print("Goodbye.")
                    break

                response = asyncio.run(assistant.chat(raw))
                print(f"K.I.D> {response.text}")
    except Exception as exc:  # pragma: no cover - CLI-facing error reporting
        print(f"K.I.D error: {exc}")
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
