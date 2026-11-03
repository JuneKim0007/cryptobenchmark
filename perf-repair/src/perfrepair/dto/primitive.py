from __future__ import annotations

from dataclasses import asdict, dataclass

from .pattern import LEGACY_VARIANT

# 2: every row carries its benchmark variant
ROWS_SCHEMA_VERSION = 2


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
    parameters: dict | None = None
    variant: str = LEGACY_VARIANT

    def to_json(self) -> dict:
        return asdict(self)

    @classmethod
    def from_json(cls, d: dict) -> "PrimitiveRow":
        return cls(**{k: d[k] if k == "variant" else d.get(k) for k in cls.__dataclass_fields__})
