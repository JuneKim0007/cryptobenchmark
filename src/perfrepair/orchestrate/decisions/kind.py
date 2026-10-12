"""The contract a decision must meet to run in the generic loop (orchestrate/runner.py).

A kind owns everything specific to one question asked of the model: what one call sees (`render`),
what an acceptable answer is (`validate`, the static gate between calls), what an answer changes
(`apply`), and what happens when no acceptable answer comes (`fallback`). The loop owns order,
retries, persistence and the journal.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Protocol


@dataclass(frozen=True)
class Checked:
    """An answer after the static gate: `decision` is set only when `problems` is empty."""
    decision: Any = None
    problems: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)


class DecisionKind(Protocol):
    name: str
    prompt: str
    schema: dict

    def render(self, item, state, refused: list[str] | None) -> str: ...

    def validate(self, item, text: str, state) -> Checked: ...

    def apply(self, item, decision, state) -> dict:
        """Change `state`; return what changed, for the journal."""

    def fallback(self, item, problems: list[str]): ...

    def decision_json(self, decision) -> dict: ...

    def decision_from_json(self, doc: dict): ...
