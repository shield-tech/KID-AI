#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$ROOT"

if [[ ! -d .venv ]]; then
  printf 'Virtual environment not found. Run ./install.sh first.\n' >&2
  exit 1
fi

source .venv/bin/activate
python main.py --voice
