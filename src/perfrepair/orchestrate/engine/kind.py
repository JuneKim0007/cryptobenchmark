"""What a decision must supply to run on the engine (orchestrate/engine/decide.py).

A kind owns what is specific to one question asked of a model: its items in a fixed order, what one
turn sees (render), what an acceptable answer is (check, gate C), what a committed record does to the
state (apply), what makes the state valid (validate, gates A and D: it must include the state being
the projection of the records), and the files that show the state (write). The engine owns order,
conversations, retries, the commit, the journal and the errors file.
"""
from __future__ import annotations

from typing import Any, Protocol

from ...dto.decision import OutboxRecord


class Item(Protocol):
    @property
    def key(self) -> str: ...


class DecisionKind(Protocol):
    name: str
    system: str
    schema: dict

    def items(self) -> list: ...

    def empty(self) -> Any: ...

    def admit(self, item) -> list[str]:
        """Gate B: the popped item is whole."""

    def label(self, item) -> str:
        """How the item is named in the errors file and progress lines."""

    def render(self, item, state) -> str: ...

    def check(self, item, text: str, state) -> tuple[dict | None, list[str]]:
        """Gate C: the decision as JSON when acceptable, else every problem."""

    def apply(self, state, item, record: OutboxRecord) -> None: ...

    def validate(self, state, records: list[OutboxRecord]) -> list[str]: ...

    def write(self, state, records: list[OutboxRecord]) -> None: ...


def project(kind: DecisionKind, records: list[OutboxRecord]):
    """The state a kind's records produce, from its empty state."""
    by_key = {i.key: i for i in kind.items()}
    state = kind.empty()
    for r in records:
        kind.apply(state, by_key[r.item], r)
    return state
