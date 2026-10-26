from __future__ import annotations

from typing import Any, Protocol

from ...dto.decision import OutboxRecord
from ...dto.prompt import TaskPrompt


class Item(Protocol):
    @property
    def key(self) -> str: ...


class DecisionKind(Protocol):
    name: str

    def items(self) -> list: ...

    def empty(self) -> Any: ...

    def admit(self, item) -> list[str]:
        """Gate B: the popped item is whole."""

    def label(self, item) -> str:
        """How the item is named in the errors file and progress lines."""

    def render(self, item, state) -> TaskPrompt: ...

    def check(self, item, text: str, state) -> tuple[dict | None, list[str]]:
        """Gate C: the decision as JSON when acceptable, else every problem."""

    def apply(self, state, item, record: OutboxRecord) -> None: ...

    def validate(self, state, records: list[OutboxRecord]) -> list[str]: ...

    def write(self, state, records: list[OutboxRecord]) -> None: ...


def project(kind: DecisionKind, records: list[OutboxRecord]):
    by_key = {i.key: i for i in kind.items()}
    state = kind.empty()
    for r in records:
        kind.apply(state, by_key[r.item], r)
    return state
