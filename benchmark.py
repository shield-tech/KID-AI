from __future__ import annotations

import os
import subprocess
from dataclasses import dataclass
from typing import Any, Optional


@dataclass
class BenchmarkResult:
    ttft_seconds: float
    total_seconds: float
    tokens_per_second: float
    success: bool = True
    error: Optional[str] = None


class BenchmarkRunner:
    def __init__(self, engine: Any) -> None:
        self.engine = engine

    async def run(self, model_name: str, prompt: str = "Benchmark K.I.D.") -> BenchmarkResult:
        import time as _time
        start = _time.perf_counter()
        first_token = None
        total_tokens = 0
        try:
            async for token in self.engine.generate(model_name, prompt, stream=True):
                if first_token is None:
                    first_token = _time.perf_counter()
                total_tokens += len(token.split())
            end = _time.perf_counter()
            ttft = (first_token - start) if first_token is not None else 0.0
            duration = max(end - start, 0.0001)
            return BenchmarkResult(
                ttft_seconds=ttft,
                total_seconds=duration,
                tokens_per_second=(total_tokens / duration) if duration else 0.0,
                success=True,
            )
        except Exception as exc:
            return BenchmarkResult(ttft_seconds=0.0, total_seconds=0.0, tokens_per_second=0.0, success=False, error=str(exc))


__all__ = ["BenchmarkRunner", "BenchmarkResult"]
