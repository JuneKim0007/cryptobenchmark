from __future__ import annotations

from dataclasses import asdict, dataclass

SCHEMA_VERSION = 1
SEVERITIES = ("error", "warning", "info")


@dataclass(frozen=True)
class Finding:
    kind: str
    severity: str
    group: str | None
    items: tuple[int, ...]
    detail: str

    def __post_init__(self):
        if self.severity not in SEVERITIES:
            raise ValueError(f"finding {self.kind}: severity {self.severity!r} is not one of {SEVERITIES}")

    def to_json(self) -> dict:
        return {**asdict(self), "items": list(self.items)}


def checks_document(findings: list[Finding]) -> dict:
    counts: dict[str, int] = {}
    for f in findings:
        counts[f.severity] = counts.get(f.severity, 0) + 1
    return {"schemaVersion": SCHEMA_VERSION, "counts": counts, "findings": [f.to_json() for f in findings]}
