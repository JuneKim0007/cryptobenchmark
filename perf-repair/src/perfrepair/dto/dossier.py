"""dossiers.json: Dossier, Option, Estimate, NoEstimate (pins null = unknown, pImprove null = n<2); noOptions reasons."""
from __future__ import annotations

import json
from dataclasses import asdict, dataclass

from .change import DROP_IN, NO_GAIN, RECOMMENDATION, PairDiff
from .perf_mode import NO_EVIDENCE
from .site import Scope

OPTION_PREFIX = "R"
NOT_ON_DEVICE = "not_on_device"
NOT_ON_DEVICE_STEP = "add it to providers.bundled in global.yaml and rerun the device stage"
NOT_ON_DEVICE_ABSENT = "absent on this device: no provider here registers it and the app ships no provider for it"
NO_REAL_USE = "no_real_use"
ENERGY_KINDS_DIFFER = "energy_kinds_differ"
ZERO_MEDIAN = "zero_median"
NO_ESTIMATE_REASONS = (ENERGY_KINDS_DIFFER, ZERO_MEDIAN)
PROVIDER_HELD_KEY = "provider_held_key"
# in filter order: a scope is in noOptions under the first filter that leaves it nothing; the last is its unit's
VARIANT_NOT_MEASURED = "variant_not_measured"
NO_OPTION_REASONS = (NO_REAL_USE, NOT_ON_DEVICE, "unresolved", VARIANT_NOT_MEASURED, "not_grouped", "no_alternative", "none_available", "deprecated_only",
                     "interop_failed", NO_GAIN, NO_EVIDENCE, PROVIDER_HELD_KEY)


def reason_code(reason: str) -> str:
    """A noOptions reason's code; `no_evidence` names its metrics after a colon."""
    return reason.split(":", 1)[0]


def pin_text(value) -> str:
    return value if isinstance(value, str) else json.dumps(value)


@dataclass(frozen=True)
class Estimate:
    """One metric of one option against the site's current choice, at the nearest measured configuration;
    pImprove is None when either side has fewer than two runs; kind: an energy estimate's measured or estimated."""
    metric: str
    ratio: float
    pImprove: float | None
    n: int
    configuration: str
    kind: str | None = None

    def to_json(self) -> dict:
        return {k: v for k, v in asdict(self).items() if k != "kind" or v is not None}


@dataclass(frozen=True)
class NoEstimate:
    """A metric both sides have that still gives no estimate."""
    metric: str
    configuration: str
    reason: str


@dataclass(frozen=True)
class Option:
    """pins None: the parameters are unknown, so no like-for-like swap can be stated; {} means nothing to pin.
    interop: the pair_status of the current item and this one. screen: its status for this app; None without screen.json.
    change: its class against the current item; diff None for a drop-in, a member of the current item's group."""
    alias: str
    item: str
    pins: dict | None
    interop: str
    estimates: tuple[Estimate, ...] = ()
    screen: str | None = None
    noEstimates: tuple[NoEstimate, ...] = ()
    change: str = DROP_IN
    diff: PairDiff | None = None
    outputChanges: bool = False
    reach: str = "unknown"
    needsReview: tuple[str, ...] = ()
    track: str = RECOMMENDATION

    def to_json(self) -> dict:
        missing = {"noEstimates": [asdict(n) for n in self.noEstimates]} if self.noEstimates else {}
        # a drop-in writes neither, so a drop-in dossier reads as it did before change classes
        changed = {"change": self.change, "diff": asdict(self.diff) if self.diff else None} if self.change != DROP_IN else {}
        return {"alias": self.alias, "item": self.item, "pins": self.pins, "interop": self.interop,
                "screen": self.screen, "estimates": [e.to_json() for e in self.estimates], "track": self.track,
                "outputChanges": self.outputChanges, "reach": self.reach, "needsReview": list(self.needsReview)} | missing | changed

    @classmethod
    def from_json(cls, d: dict) -> "Option":
        diff = PairDiff(**d["diff"]) if d.get("diff") else None
        return cls(d["alias"], d["item"], d["pins"], d["interop"], tuple(Estimate(**e) for e in d.get("estimates") or ()),
                   d["screen"], tuple(NoEstimate(**n) for n in d.get("noEstimates") or ()), d.get("change", DROP_IN), diff,
                   d["outputChanges"], d["reach"], tuple(d["needsReview"]), d["track"])


@dataclass(frozen=True)
class Dossier:
    """What the replacement decision sees for one scope: the code, the current item and the interchangeable options."""
    scope: Scope
    source: str
    current: str
    options: tuple[Option, ...]
    # prepared.yaml perCall of the current item's rows in the scope's variant; empty before variants
    perCall: tuple[str, ...] = ()

    @property
    def key(self) -> str:
        return self.scope.id

    def to_json(self) -> dict:
        return {"scope": self.scope.to_json(), "source": self.source, "current": self.current,
                "options": [o.to_json() for o in self.options], "perCall": list(self.perCall)}

    @classmethod
    def from_json(cls, d: dict) -> "Dossier":
        return cls(Scope.from_json(d["scope"]), d["source"], d["current"], tuple(Option.from_json(o) for o in d["options"]),
                   tuple(d.get("perCall") or ()))
