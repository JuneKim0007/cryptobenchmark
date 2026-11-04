"""The one finding shape every invariant returns: id, severity, subject, evidence, fix."""
from __future__ import annotations

from dataclasses import asdict, dataclass

BLOCKING, ADVISORY, UNDECIDED = "blocking", "advisory", "undecided"
SEVERITIES = (BLOCKING, ADVISORY, UNDECIDED)


@dataclass(frozen=True)
class Violation:
    """evidence: `file:line` or `group <id>` entries; undecided: the rule could not be read from the artifacts or source."""
    invariant: str
    severity: str
    subject: str
    evidence: tuple[str, ...]
    fix: str

    def __post_init__(self):
        if self.severity not in SEVERITIES:
            raise ValueError(f"{self.invariant}: severity {self.severity!r} is not one of {SEVERITIES}")

    def to_json(self) -> dict:
        return asdict(self) | {"evidence": list(self.evidence)}

    def line(self) -> str:
        return f"{self.severity} {self.invariant} {self.subject}: {'; '.join(self.evidence)} -> {self.fix}"


def blocking(found: list[Violation]) -> list[Violation]:
    return [v for v in found if v.severity == BLOCKING]


def counts(found: list[Violation]) -> dict[str, dict[str, int]]:
    out: dict[str, dict[str, int]] = {}
    for v in found:
        out.setdefault(v.invariant, {}).setdefault(v.severity, 0)
        out[v.invariant][v.severity] += 1
    return dict(sorted(out.items()))
