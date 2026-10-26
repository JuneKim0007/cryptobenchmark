from types import SimpleNamespace

import pytest
from helpers import task

from perfrepair.dto.prompt import SystemPrompt
from perfrepair.ai.runtime.agent import AgentRefused, ClaudeConversations


class FakeMessages:
    def __init__(self, stop_reason="end_turn"):
        self.kwargs, self.stop_reason = None, stop_reason

    def create(self, **kwargs):
        self.kwargs = {**kwargs, "messages": list(kwargs["messages"])}
        return SimpleNamespace(
            stop_reason=self.stop_reason, stop_details=SimpleNamespace(explanation="declined"),
            content=[SimpleNamespace(type="text", text="{}")], model=kwargs["model"],
            usage=SimpleNamespace(input_tokens=10, output_tokens=5, cache_read_input_tokens=8,
                                  cache_creation_input_tokens=0))


def test_one_turn_cached_system_and_schema():
    messages, schema = FakeMessages(), {"type": "object"}
    reply = ClaudeConversations(client=SimpleNamespace(messages=messages)).start(SystemPrompt("t", "SYS"), schema).ask(task("ITEM"))
    k = messages.kwargs
    assert k["messages"] == [{"role": "user", "content": "ITEM"}]
    assert k["system"][0]["cache_control"] == {"type": "ephemeral"}
    assert k["output_config"]["format"]["schema"] is schema
    assert reply.usage["cacheRead"] == 8


def test_refusal_raises():
    with pytest.raises(AgentRefused):
        ClaudeConversations(client=SimpleNamespace(messages=FakeMessages("refusal"))).start(SystemPrompt("t", "SYS"), {}).ask(task("ITEM"))
