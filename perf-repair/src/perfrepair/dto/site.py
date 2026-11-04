from __future__ import annotations

import hashlib
from dataclasses import asdict, dataclass

from .lifecycle import Lifecycle
from .metrics import NAMES
from .pattern import NOT_FIXED, UNKNOWN_DEFAULT

# one per artifact, so a change to one file never moves another's reader
APP_SCHEMA_VERSION = 1
SITES_SCHEMA_VERSION = 1
EDITS_SCHEMA_VERSION = 1
# 2: `units`, the units asked, each member with a dossier; 3: `perfMode`, estimates of its metrics only
# 4: `maxChange` and `notOffered`; an option above drop-in carries its change class and pair diff
# 5: every option carries track, outputChanges, reach and needsReview
# 6: estimates of the scope's pattern's variant only; perCall, what its current item's timed call redoes
DOSSIERS_SCHEMA_VERSION = 6
# 2: each scope carries its lifecycle; 3: requirements and the use carry their completion; 4: a requirement carries only what code settled
# 5: pattern, patternReason and patternLines on every scope
SCOPES_SCHEMA_VERSION = 5
# 2: set_algorithm carries its name in Edit.algorithm, not parameters.algorithm; 3: stale, the scopes decided on an earlier dossier
# 4: recommend with needs; deciding, accepted and concerns on every row
REPLACEMENTS_SCHEMA_VERSION = 4
# 3: imports are the ones the function uses; notMeasurable refuses a scope a number would misdescribe; 4: inverse, the interop partner by link
HARNESS_SCHEMA_VERSION = 4
NO_OPERATION = "no_operation"
NOT_MEASURABLE_REASONS = (NO_OPERATION,)
INPUT_SOURCES = ("app", "run")
SINKS = ("persist", "network", "return", "local", "unknown")
KEY_SOURCES = ("keystore", "generated", "derived", "storage", "literal", "parameter", "unknown")
METRICS = NAMES


def scope_id(app: str, file: str, function: str, line: int, call: str) -> str:
    return hashlib.sha256("\0".join([app, file, function, str(line), call]).encode()).hexdigest()[:12]


@dataclass(frozen=True)
class Scope:
    """One call site and the function around it; the unit every layer after detection works on."""
    id: str
    app: str
    file: str
    line: int
    call: str
    function: str
    start: int
    end: int
    engineType: str
    algorithm: str | None
    provider: str | None
    resolution: str
    keySize: int | None = None
    inputSize: int | None = None
    sinks: tuple[str, ...] = ("unknown",)
    keySource: str = "unknown"
    lifecycle: Lifecycle | None = None
    # the divergence category scope/pattern.py gives, its rule's reason and the lines that decided it
    pattern: str = NOT_FIXED
    patternReason: str = UNKNOWN_DEFAULT
    patternLines: tuple[int, ...] = ()

    def to_json(self) -> dict:
        return asdict(self) | {"sinks": list(self.sinks), "patternLines": list(self.patternLines),
                               "lifecycle": self.lifecycle.to_json() if self.lifecycle is not None else None}

    @classmethod
    def from_json(cls, d: dict) -> "Scope":
        lifecycle = Lifecycle.from_json(d["lifecycle"]) if d.get("lifecycle") is not None else None
        return cls(**{**d, "sinks": tuple(d.get("sinks") or ("unknown",)), "lifecycle": lifecycle,
                      "patternLines": tuple(d.get("patternLines") or ())})
