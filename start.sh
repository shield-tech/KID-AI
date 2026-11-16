#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$ROOT"

if [[ ! -x .venv/bin/python ]]; then
  printf 'K.I.D virtual environment missing. Run ./install.sh first.\n' >&2
  exit 1
fi

if [[ ! -f .env ]]; then
  printf 'No .env found; using built-in safe defaults. Copy .env.example to .env to configure.\n'
fi

exec .venv/bin/python main.py "$@"
