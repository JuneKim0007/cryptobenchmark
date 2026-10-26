from types import SimpleNamespace

import pytest
from helpers import task

from perfrepair.dto.prompt import CorrectionPrompt, SystemPrompt
from perfrepair.ai.runtime.agent import AgentRefused, ClaudeClient, ClaudeConversations


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


def test_a_correction_resends_the_history_under_the_same_cached_system():
    messages = FakeMessages()
    convo = ClaudeConversations(client=SimpleNamespace(messages=messages)).start(SystemPrompt("t", "SYS"), {})
    convo.ask(task("ITEM"))
    convo.ask(CorrectionPrompt("t", "FIX"))
    k = messages.kwargs
    assert [m["content"] for m in k["messages"] if m["role"] == "user"] == ["ITEM", "FIX"]
    assert k["system"] == [{"type": "text", "text": "SYS", "cache_control": {"type": "ephemeral"}}]


def test_only_run_lifetime_text_is_cached():
    messages = FakeMessages()
    ClaudeClient(client=SimpleNamespace(messages=messages)).request(task("PER-ITEM"), [{"role": "user", "content": "x"}], {})
    assert messages.kwargs["system"] == [{"type": "text", "text": "PER-ITEM"}]
