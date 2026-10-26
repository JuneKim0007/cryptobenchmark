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


def fill(text: str, values: dict) -> str:
    for key, value in values.items():
        text = text.replace("{" + key + "}", str(value))
    return text


@dataclass(frozen=True)
class Charter:
    """What every conversation of a run shares; the fingerprint hashes the system prompt, schema and correction template."""
    system: SystemPrompt
    schema: dict
    correction: CorrectionPrompt  # unfilled: correct() fills {problems}

    @property
    def prompts(self) -> tuple[str, ...]:
        return self.system.name, self.correction.name

    def correct(self, problems: list[str]) -> CorrectionPrompt:
        return CorrectionPrompt(self.correction.name,
                                fill(self.correction.text, {"problems": "\n".join(f"  - {p}" for p in problems)}))

    @property
    def fingerprint(self) -> str:
        body = "\0".join([self.system.text, json.dumps(self.schema, sort_keys=True), self.correction.text])
        return hashlib.sha256(body.encode()).hexdigest()[:12]
