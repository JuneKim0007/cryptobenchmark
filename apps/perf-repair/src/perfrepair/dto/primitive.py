from __future__ import annotations

from dataclasses import asdict, dataclass, field

from .document import DocumentKind

# 2: every row carries its benchmark variant and perCall
ROWS_SCHEMA_VERSION = 2
ROWS_DOC = DocumentKind("rows", ROWS_SCHEMA_VERSION)


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
    # validation/rows.py refuses a case without one
    variant: str | None = field(kw_only=True)
    # prepared.yaml's perCall: what one timed call redoes
    perCall: str | None = None
    # the delta session that measured it, None for the benchmark's own; drift: its anchors moved past the noise rule
    session: str | None = None
    drift: bool = False

    def to_json(self) -> dict:
        return asdict(self)

    @classmethod
    def from_json(cls, d: dict) -> "PrimitiveRow":
        return cls(**{k: d[k] if k == "variant" else d.get(k, False) if k == "drift" else d.get(k)
                      for k in cls.__dataclass_fields__})
