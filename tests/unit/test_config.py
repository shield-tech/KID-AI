import asyncio

from kid.core.assistant import KIDAssistant
from kid.core.models import GenerationOptions, Message, ProviderResponse


class FakeProvider:
    def __init__(self):
        self.model = "fake-model"
        self.temperature = 0.2
        self.max_tokens = 64

    async def generate(self, messages, options):
        assert isinstance(messages[0], Message)
        assert messages[0].role == "system"
        assert messages[-1].role == "user"
        return ProviderResponse(
            text=f"Echo: {messages[-1].content}",
            provider="fake",
        )


def test_assistant_routes_message_and_returns_response():
    assistant = KIDAssistant(FakeProvider(), system_prompt="You are K.I.D")

    response = asyncio.run(assistant.chat("Hello there"))

    assert response.text == "Echo: Hello there"
    assert response.provider == "fake"
