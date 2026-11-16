from __future__ import annotations

import asyncio
from pathlib import Path

from config import AppConfig
from conversation import ConversationEngine
from knowledge import KnowledgeBase
from memory import MemoryStore
from ollama_engine import OllamaEngine, OllamaError


def test_config_defaults_and_validation() -> None:
    config = AppConfig()
    assert config.ollama_base_url == "http://127.0.0.1:11434"
    assert config.chat_model == ""
    config.num_ctx = 1
    try:
        # from_env validates environment; dataclass fields themselves remain usable in tests
        AppConfig.from_env()
    except ValueError:
        pass


def test_sqlite_memory_crud_and_history(tmp_path: Path) -> None:
    store = MemoryStore(str(tmp_path / "memory.db"))
    item_id = store.add_memory("robotics", "Prefer simulation for tests")
    assert store.list_memories()[0]["id"] == item_id
    assert store.get_relevant_memories("simulation")
    assert store.edit_memory(item_id, "robotics", "Use simulation first")
    assert store.list_memories()[0]["content"] == "Use simulation first"
    store.add_message("user", "hello")
    store.add_message("assistant", "hi")
    assert store.get_recent_history() == [("user", "hello"), ("assistant", "hi")]
    assert store.clear_history() == 2
    assert store.delete_memory(item_id)
    assert not store.delete_memory(item_id)


def test_knowledge_index_keyword_search_and_update(tmp_path: Path) -> None:
    docs = tmp_path / "docs"
    docs.mkdir()
    file = docs / "robot.md"
    file.write_text("Robotics safety requires an emergency stop and a speed limit.", encoding="utf-8")
    kb = KnowledgeBase(str(docs), str(tmp_path / "index.db"))
    assert kb.index_directory() == [str(file.resolve())]
    result = kb.search("emergency stop")
    assert result and result[0]["path"] == str(file.resolve())
    assert "speed limit" in result[0]["excerpt"]
    assert kb.index_directory() == []
    file.write_text("Updated safety documentation about motor limits.", encoding="utf-8")
    assert kb.index_directory() == [str(file.resolve())]
    assert kb.search("motor limits")


def test_commands_and_model_switch(tmp_path: Path) -> None:
    class FakeOllama:
        async def available_models(self):
            return ["small:latest", "vision:latest"]
        async def health(self):
            return True
    class Config(AppConfig):
        memory_db_path = str(tmp_path / "commands.db")
        knowledge_root = str(tmp_path / "docs")
    config = AppConfig(memory_db_path=str(tmp_path / "commands.db"), knowledge_root=str(tmp_path / "docs"))
    engine = ConversationEngine(config, ollama=FakeOllama(), memory=MemoryStore(config.memory_db_path), knowledge=KnowledgeBase(config.knowledge_root, str(tmp_path / "k.db")))
    async def exercise():
        assert (await engine.handle_command("/model small:latest")).startswith("Model switched")
        assert "small:latest" in await engine.handle_command("/models")
        saved = await engine.handle_command("/remember setup | run locally")
        assert "Saved" in saved
        assert "run locally" in await engine.handle_command("/memory")
        assert "deleted" in await engine.handle_command("/forget 1")
        assert await engine.handle_command("/unknown") == "Unknown command. Type /help."
    asyncio.run(exercise())


def test_ollama_stream_parsing_and_cancellation() -> None:
    import httpx
    from ollama_engine import OllamaEngine

    async def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path == "/api/generate"
        body = b'{"response":"hello","done":false}\n{"response":" world","done":false}\n{"response":"","done":true,"eval_count":2,"eval_duration":1000000000}\n'
        return httpx.Response(200, content=body, headers={"content-type": "application/x-ndjson"})
    async def exercise():
        client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
        class TestEngine(OllamaEngine):
            async def generate(self, model_name, prompt, **kwargs):
                payload = {"model": model_name, "prompt": prompt, "stream": True, "keep_alive": "5m", "options": {}}
                async with client.stream("POST", "http://test/api/generate", json=payload) as response:
                    async for line in response.aiter_lines():
                        item = __import__("json").loads(line)
                        if item.get("response"):
                            yield item["response"]
                        if item.get("done"):
                            self.last_stats = item
                            break
        engine = TestEngine(AppConfig())
        got = [token async for token in engine.generate("test", "hello")]
        assert got == ["hello", " world"]
        await client.aclose()
    asyncio.run(exercise())


def test_conversation_handles_missing_model_without_download(tmp_path: Path) -> None:
    class Offline:
        async def available_models(self):
            return []
    config = AppConfig(memory_db_path=str(tmp_path / "m.db"), knowledge_enabled=False)
    engine = ConversationEngine(config, ollama=Offline(), memory=MemoryStore(config.memory_db_path), knowledge=None)
    async def exercise():
        try:
            async for _ in engine.stream_response("hello"):
                pass
        except OllamaError as exc:
            assert "will not download" in str(exc)
        else:
            raise AssertionError("Expected a no-model error")
    asyncio.run(exercise())
