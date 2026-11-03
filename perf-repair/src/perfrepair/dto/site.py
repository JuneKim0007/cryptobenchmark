from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass, fields

from .lifecycle import Lifecycle

SCHEMA_VERSION = 1
# 2: each scope carries its lifecycle; 3: requirements and the use carry their completion
SCOPES_SCHEMA_VERSION = 3
# 2: set_algorithm carries its name in Edit.algorithm, not parameters.algorithm; 3: stale, the scopes decided on an earlier dossier
REPLACEMENTS_SCHEMA_VERSION = 3
# 3: imports are the ones the function uses; notMeasurable refuses a scope a number would misdescribe
HARNESS_SCHEMA_VERSION = 3
NO_OPERATION = "no_operation"
NOT_MEASURABLE_REASONS = (NO_OPERATION,)
INPUT_SOURCES = ("app", "run")
SINKS = ("persist", "network", "return", "local", "unknown")
KEY_SOURCES = ("keystore", "generated", "derived", "storage", "literal", "parameter", "unknown")
DECISIONS = ("replace", "keep")
OPTION_PREFIX = "R"
METRICS = ("timeNs", "allocationCount", "energyJ")
NOT_ON_DEVICE = "not_on_device"
NOT_ON_DEVICE_STEP = "add it to providers.bundled in global.yaml and rerun the device stage"
NO_REAL_USE = "no_real_use"
# in filter order: a scope is in noOptions under the first filter that leaves it nothing
NO_OPTION_REASONS = (NO_REAL_USE, NOT_ON_DEVICE, "unresolved", "not_grouped", "no_alternative", "none_available", "deprecated_only",
                     "interop_failed")
RISKS = ("persisted_data", "wire_format", "key_compatibility", "unknown_sink", "unverified_interop")
# (scope or option field, value, risk it implies, plain words): the minimum risks a replace must declare
DERIVED_RISKS = (
    ("sinks", "persist", "persisted_data", "the output is stored and read back later"),
    ("sinks", "network", "wire_format", "the output leaves the process"),
    ("sinks", "unknown", "unknown_sink", "where the output goes is unknown"),
    ("keySource", "keystore", "key_compatibility", "the key lives in a key store"),
    ("keySource", "literal", "key_compatibility", "the key is a literal in the code"),
    ("keySource", "storage", "key_compatibility", "the key is read back from storage"),
    ("interop", "not_checkable", "unverified_interop", "the interop check could not decide the pair"),
    ("interop", "not_planned", "unverified_interop", "the pair was not in the interop plan"),
    ("interop", "not_run", "unverified_interop", "no interop check has run"),
)


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

    def to_json(self) -> dict:
        return asdict(self) | {"sinks": list(self.sinks),
                               "lifecycle": self.lifecycle.to_json() if self.lifecycle is not None else None}

    @classmethod
    def from_json(cls, d: dict) -> "Scope":
        lifecycle = Lifecycle.from_json(d["lifecycle"]) if d.get("lifecycle") is not None else None
        return cls(**{**d, "sinks": tuple(d.get("sinks") or ("unknown",)), "lifecycle": lifecycle})


def required_risks(scope: Scope, option: "Option | None" = None) -> dict[str, list[str]]:
    """Each risk the scope facts, and the chosen option's when given, imply, with the plain words that imply it."""
    out: dict[str, list[str]] = {}
    option_fields = {f.name for f in fields(Option)}
    for field_name, value, risk, words in DERIVED_RISKS:
        subject = option if field_name in option_fields else scope
        facts = getattr(subject, field_name) if subject is not None else ()
        if value in (facts if isinstance(facts, tuple) else (facts,)):
            out.setdefault(risk, []).append(words)
    return out


def pin_text(value) -> str:
    return value if isinstance(value, str) else json.dumps(value)


@dataclass(frozen=True)
class Estimate:
    """One metric of one option against the site's current choice, at the nearest measured configuration;
    pImprove is None when either side has fewer than two runs."""
    metric: str
    ratio: float
    pImprove: float | None
    n: int
    configuration: str


@dataclass(frozen=True)
class Option:
    """pins None: the parameters are unknown, so no like-for-like swap can be stated; {} means nothing to pin.
    interop: the pair_status of the current item and this one. screen: its status for this app; None without screen.json."""
    alias: str
    item: str
    pins: dict | None
    interop: str
    estimates: tuple[Estimate, ...] = ()
    screen: str | None = None

    def to_json(self) -> dict:
        return {"alias": self.alias, "item": self.item, "pins": self.pins, "interop": self.interop,
                "screen": self.screen, "estimates": [asdict(e) for e in self.estimates]}

    @classmethod
    def from_json(cls, d: dict) -> "Option":
        return cls(d["alias"], d["item"], d["pins"], d["interop"], tuple(Estimate(**e) for e in d.get("estimates") or ()),
                   d["screen"])


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
class EditKind:
    """`field` of an Edit is the one this kind fills, with the chosen option's `takes`; the other fields stay empty."""
    field: str
    takes: str
    phrase: str
    meaning: str
    value: str
    required: str


EDIT_FIELDS = ("provider", "algorithm", "parameters")
EDIT_KIND_TABLE = {
    "set_provider": EditKind("provider", "provider", "is provided by",
                             "construct the call's engine from the chosen option's provider", "that name exactly",
                             "when the option's provider differs from the current one"),
    "set_algorithm": EditKind("algorithm", "algorithm", "is named",
                              "request the chosen option's name instead of the current one", "that name exactly",
                              "when the option's name differs from the current one"),
    "pin_parameters": EditKind("parameters", "pins", "lists",
                               "state the option's pins at the call so the result stays like-for-like",
                               "every pin as {name, value}, exactly as listed",
                               "when the option lists pins; not allowed when it lists none"),
}
EDIT_KINDS = tuple(EDIT_KIND_TABLE)


@dataclass(frozen=True)
class Edit:
    kind: str
    provider: str | None = None
    algorithm: str | None = None
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


def read_replacements(doc: dict) -> dict[str, Replacement]:
    if doc.get("schemaVersion") != REPLACEMENTS_SCHEMA_VERSION:
        raise ValueError(f"replacements schemaVersion {doc.get('schemaVersion')} is not {REPLACEMENTS_SCHEMA_VERSION}")
    return {r["scope"]: Replacement.from_json(r) for r in doc["replacements"]}
