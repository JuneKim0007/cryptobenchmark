from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable, Mapping

from ..agent.conversation import Conversations


@dataclass(frozen=True)
class Gateway:
    """settings: a frozen dataclass; its fields, each with a default, are the block's keys, its __post_init__ their check."""
    name: str
    settings: type
    # values, and the role's dry-run answers, which only a stand-in gateway answers with
    spawn: Callable[[Any, Conversations], Conversations]
    secret: Callable[[Any], str | None] = lambda _: None
    choices: Mapping[str, tuple[str, ...]] = field(default_factory=dict)
