from __future__ import annotations

from dataclasses import asdict, dataclass


@dataclass(frozen=True)
class PrimitiveRow:
    rowId: str                 # the benchmark case id; PlanCheck refuses duplicates, so it is unique per run
    type: str
    algorithm: str
    provider: str
    operation: str
    keySize: int | None
    inputSize: int | None
    phase: str | None
    keyKind: str | None = None

    def to_json(self) -> dict:
        return asdict(self)

    @classmethod
    def from_json(cls, d: dict) -> "PrimitiveRow":
        return cls(**{k: d.get(k) for k in cls.__dataclass_fields__})
