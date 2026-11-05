import pytest
from helpers import SYSTEM, task

from perfrepair.dto.prompt import CorrectionPrompt
from perfrepair.ai.runtime.agent import ScriptedConversations

FIX = CorrectionPrompt("test", "fix it")


def scripted():
    return ScriptedConversations(lambda t, session, turn: {"item": t.item, "turn": turn})


@pytest.mark.parametrize("system", ["SYS", task("SYS"), FIX])
def test_a_conversation_starts_only_with_a_system_prompt(system):
    with pytest.raises(TypeError, match="lifetime_mismatch"):
        scripted().start(system, {})


@pytest.mark.parametrize("first", ["raw text", FIX])
def test_the_first_turn_takes_only_a_task_prompt(first):
    with pytest.raises(TypeError, match="lifetime_mismatch"):
        scripted().start(SYSTEM, {}).ask(first)


def test_a_rejected_turn_is_not_recorded_and_the_session_continues():
    agent = scripted()
    convo = agent.start(SYSTEM, {})
    convo.ask(task("first", item="a"))
    with pytest.raises(TypeError):
        convo.ask(task("again"))
    assert convo.ask(FIX).text == '{"item": "a", "turn": 2}'
    assert [(n, t, m.text) for n, t, m in agent.turns] == [(1, 1, "first"), (1, 2, "fix it")]
    assert agent.systems == [SYSTEM]
