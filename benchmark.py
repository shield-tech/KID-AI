from __future__ import annotations

import time
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
        start = time.perf_counter()
        first_token = None
        try:
            async for _token in self.engine.generate(model_name, prompt):
                if first_token is None:
                    first_token = time.perf_counter()
            end = time.perf_counter()
            duration = max(end - start, 1e-9)
            stats = self.engine.last_stats
            count = int(stats.get("eval_count", 0) or 0)
            eval_duration = int(stats.get("eval_duration", 0) or 0) / 1e9
            rate = count / eval_duration if eval_duration > 0 else 0.0
            return BenchmarkResult((first_token - start) if first_token else 0.0, duration, rate)
        except Exception as exc:
            return BenchmarkResult(0.0, time.perf_counter() - start, 0.0, False, str(exc))


__all__ = ["BenchmarkRunner", "BenchmarkResult"]
