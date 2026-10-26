from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from enum import Enum
from typing import Callable, ClassVar


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


@dataclass(frozen=True)
class Charter:
    """What every conversation of a run shares; its fingerprint names the run's answers."""
    system: SystemPrompt
    schema: dict
    correction: str
    correct: Callable[[list[str]], CorrectionPrompt] = field(compare=False, repr=False)

    @property
    def fingerprint(self) -> str:
        body = "\0".join([self.system.text, json.dumps(self.schema, sort_keys=True), self.correction])
        return hashlib.sha256(body.encode()).hexdigest()[:12]
