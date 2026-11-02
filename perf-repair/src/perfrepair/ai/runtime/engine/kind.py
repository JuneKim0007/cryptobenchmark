from __future__ import annotations

from typing import Any, Protocol

from ....dto.decision import OutboxRecord
from ....dto.prompt import TaskPrompt


class Item(Protocol):
    @property
    def key(self) -> str: ...


class DecisionKind(Protocol):
    name: str

    def items(self) -> list:
        """Every item a record may name: the lookup list of projections and replay."""

    def pending(self) -> list:
        """The items to ask, a subset of items(); a kind that settles none in code returns items()."""

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


def replay_problems(kind: DecisionKind, state, records: list[OutboxRecord]) -> list[str]:
    """The state is one version per committed record and equals the projection of the outbox."""
    noun = type(state).__name__.lower()
    problems = [] if state.version == len(records) else [
        f"{noun} version {state.version} is not the {len(records)} records committed"]
    try:
        # to_json: a saved state reloads with sorted lists the replay need not have
        if project(kind, records).to_json() != state.to_json():
            problems.append(f"{noun} differs from the replay of the outbox")
    except (KeyError, ValueError, TypeError) as e:
        problems.append(f"outbox does not replay: {e!r}")
    return problems
