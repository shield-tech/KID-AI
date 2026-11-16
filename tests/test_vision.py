from __future__ import annotations

import asyncio
from pathlib import Path

from config import AppConfig
from vision import VisionManager


class FakeOllama:
    base_url = "http://127.0.0.1:11434"
    async def available_models(self):
        return ["vision-model"]
    async def model_info(self, model):
        return {"capabilities": ["completion", "vision"]}


def test_vision_requires_reported_capability_and_supports_local_image(tmp_path: Path, monkeypatch) -> None:
    import httpx
    image = tmp_path / "sample.png"
    image.write_bytes(b"not-real-png-but-image-bytes")
    captured = {}
    async def handler(request: httpx.Request) -> httpx.Response:
        import json
        captured.update(json.loads(request.content))
        return httpx.Response(200, json={"message": {"content": "A test image description."}})
    manager = VisionManager(FakeOllama(), AppConfig())
    client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
    class TestVision(VisionManager):
        async def _request(self, *args, **kwargs):
            return "unused"
    async def exercise():
        monkeypatch.setattr("httpx.AsyncClient", lambda **kwargs: client)
        result = await manager.analyze("vision-model", str(image), "Describe")
        assert result == "A test image description."
        assert captured["messages"][0]["images"]
        assert captured["model"] == "vision-model"
        await client.aclose()
    asyncio.run(exercise())


def test_vision_rejects_unverified_model_and_oversize_file(tmp_path: Path) -> None:
    class NoVision(FakeOllama):
        async def model_info(self, model):
            return {"capabilities": ["completion"]}
    image = tmp_path / "x.png"
    image.write_bytes(b"image")
    manager = VisionManager(NoVision(), AppConfig())
    async def exercise():
        assert "not verified" in await manager.analyze("vision-model", str(image))
        large = tmp_path / "big.png"
        with large.open("wb") as handle:
            handle.truncate(20 * 1024 * 1024 + 1)
        assert "20 MiB" in await VisionManager(FakeOllama(), AppConfig()).analyze("vision-model", str(large))
    asyncio.run(exercise())
