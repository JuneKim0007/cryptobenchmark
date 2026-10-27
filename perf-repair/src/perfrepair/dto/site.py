from __future__ import annotations

import hashlib
from dataclasses import asdict, dataclass, field

SCHEMA_VERSION = 1
SINKS = ("persist", "network", "return", "local", "unknown")
KEY_SOURCES = ("keystore", "generated", "derived", "literal", "parameter", "unknown")
EDIT_KINDS = ("set_provider", "pin_parameters")
DECISIONS = ("replace", "keep")
METRICS = ("timeNs", "allocationCount", "energyUj")


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

    def to_json(self) -> dict:
        return asdict(self) | {"sinks": list(self.sinks)}

    @classmethod
    def from_json(cls, d: dict) -> "Scope":
        return cls(**{**d, "sinks": tuple(d.get("sinks") or ("unknown",))})


@dataclass(frozen=True)
class Estimate:
    """One metric of one option against the site's current choice, at the nearest measured configuration."""
    metric: str
    ratio: float
    pImprove: float
    n: int
    configuration: str


@dataclass(frozen=True)
class Option:
    alias: str
    item: str
    pins: dict = field(default_factory=dict)
    estimates: tuple[Estimate, ...] = ()

    def to_json(self) -> dict:
        return {"alias": self.alias, "item": self.item, "pins": self.pins, "estimates": [asdict(e) for e in self.estimates]}

    @classmethod
    def from_json(cls, d: dict) -> "Option":
        return cls(d["alias"], d["item"], d.get("pins") or {}, tuple(Estimate(**e) for e in d.get("estimates") or ()))


@dataclass(frozen=True)
class Dossier:
    """What the replacement decision sees for one scope: the code, the current item and the interchangeable options."""
    scope: Scope
    source: str
    current: str
    options: tuple[Option, ...]

    @property
    def key(self) -> str:
        return self.scope.id

    def to_json(self) -> dict:
        return {"scope": self.scope.to_json(), "source": self.source, "current": self.current,
                "options": [o.to_json() for o in self.options]}

    @classmethod
    def from_json(cls, d: dict) -> "Dossier":
        return cls(Scope.from_json(d["scope"]), d["source"], d["current"], tuple(Option.from_json(o) for o in d["options"]))


@dataclass(frozen=True)
class Edit:
    kind: str
    provider: str | None = None
    parameters: dict | None = None


@dataclass(frozen=True)
class Replacement:
    """The model's decision for one scope, after its gate: which option, and the edits from EDIT_KINDS that apply it."""
    scope: str
    decision: str
    option: str | None
    edits: tuple[Edit, ...]
    risks: tuple[str, ...]
    reason: str

    def to_json(self) -> dict:
        return {"scope": self.scope, "decision": self.decision, "option": self.option,
                "edits": [asdict(e) for e in self.edits], "risks": list(self.risks), "reason": self.reason}

    @classmethod
    def from_json(cls, d: dict) -> "Replacement":
        return cls(d["scope"], d["decision"], d.get("option"), tuple(Edit(**e) for e in d.get("edits") or ()),
                   tuple(d.get("risks") or ()), d["reason"])
