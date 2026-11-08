"""One tool shape: a name, one line of description, a small schema, its kind and the code that runs it."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable

READ, SUBMIT = "read", "submit"
KINDS = (READ, SUBMIT)


@dataclass(frozen=True)
class Outcome:
    ok: bool
    # what the model sees: the read's text, "accepted", or the problems
    text: str
    # a submit's accepted decision
    value: dict | None = None


@dataclass
class Context:
    """One conversation's calls: which job and item, every call in order, and what a submit accepted."""
    job: str
    item: str
    calls: list[dict] = field(default_factory=list)
    submitted: dict | None = None


@dataclass(frozen=True)
class Tool:
    name: str
    description: str
    schema: dict
    kind: str
    run: Callable[[dict, Context], Outcome] = field(compare=False)

    def __post_init__(self):
        if self.kind not in KINDS:
            raise ValueError(f"tool {self.name}: kind {self.kind!r} is not one of {KINDS}")

    def definition(self) -> dict[str, Any]:
        return {"name": self.name, "description": self.description, "input_schema": self.schema}


def args_schema(properties: dict, required: tuple[str, ...] = ()) -> dict:
    return {"type": "object", "properties": properties, "required": list(required), "additionalProperties": False}
