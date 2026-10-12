"""Agents that call no model: a fixed answer for dry runs, a scripted one for tests."""
from __future__ import annotations

import json
from typing import Callable

from .reply import AgentReply


class FixedAgent:
    """Dry run: the same answer for every item; exercises the loop, validation and files at zero cost."""

    def __init__(self, answer: dict):
        self.answer = answer

    def __call__(self, system: str, user: str, schema: dict) -> AgentReply:
        return AgentReply(json.dumps(self.answer), "dry-run")


class ScriptedAgent:
    """Answers from a function of the user message and records every call it receives."""

    def __init__(self, answer: Callable[[str], dict | str]):
        self.answer, self.calls = answer, []

    def __call__(self, system: str, user: str, schema: dict) -> AgentReply:
        self.calls.append((system, user))
        out = self.answer(user)
        return AgentReply(out if isinstance(out, str) else json.dumps(out), "scripted")
