from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from enum import Enum
from typing import ClassVar


class Lifetime(Enum):
    RUN = "run"
    SESSION = "session"
    TURN = "turn"


@dataclass(frozen=True)
class Prompt:
    lifetime: ClassVar[Lifetime]
    name: str
    text: str

    def __post_init__(self):
        if type(self) is Prompt:
            raise TypeError("Prompt is a base: build a SystemPrompt, TaskPrompt or CorrectionPrompt")

    @property
    def digest(self) -> str:
        return hashlib.sha256(self.text.encode()).hexdigest()


@dataclass(frozen=True)
class SystemPrompt(Prompt):
    lifetime = Lifetime.RUN


@dataclass(frozen=True)
class TaskPrompt(Prompt):
    lifetime = Lifetime.SESSION
    item: str


@dataclass(frozen=True)
class CorrectionPrompt(Prompt):
    lifetime = Lifetime.TURN


def fingerprint(system: SystemPrompt, schema: dict) -> str:
    """What a run's answers depend on besides the item: the system prompt and the answer schema."""
    body = system.text + "\0" + json.dumps(schema, sort_keys=True)
    return hashlib.sha256(body.encode()).hexdigest()[:12]
