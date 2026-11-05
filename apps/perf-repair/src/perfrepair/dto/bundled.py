"""Providers the target apps ship that the device lacks, and bundled-suggestions.yaml (schema 1): each matched to a
catalog row, blocked, or unmatched with a reason."""
from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass, field

from .version import newest

SCHEMA_VERSION = 1
WARN, STOP = "warn", "stop"
OFF, SUGGEST, APPLY = "off", "suggest", "apply"
FROM_APPS = (OFF, SUGGEST, APPLY)
NO_CATALOG_ROW, NO_COORDINATES, NO_PINNED_VERSION, NAME_TAKEN = ("no_catalog_row", "no_coordinates", "no_pinned_version",
                                                                  "name_taken")
UNMATCHED_REASONS = (NO_CATALOG_ROW, NO_COORDINATES, NO_PINNED_VERSION, NAME_TAKEN)


@dataclass(frozen=True)
class BundledPolicy:
    """device.bundled.fromApps: what the catalog's rows are used for; a missing provider is stops.bundled_missing."""
    fromApps: str = OFF

    @classmethod
    def read(cls, from_apps: str | bool) -> "BundledPolicy":
        return cls(OFF if from_apps is False else from_apps)


@dataclass(frozen=True)
class Coordinate:
    """One group:name that ships the provider; pins: per app its pinned version, None when its build files pin none."""
    artifact: str
    pins: tuple[tuple[str, str | None], ...]

    @property
    def version(self) -> str | None:
        return newest(v for _, v in self.pins)

    @property
    def apps(self) -> tuple[str, ...]:
        return tuple(a for a, _ in self.pins)

    def text(self) -> str:
        return f"{self.artifact}:{self.version}" if self.version else f"{self.artifact} (no pinned version)"


@dataclass(frozen=True)
class MissingProvider:
    """sites: the target sites that name it and resolved not_on_device."""
    provider: str
    apps: tuple[str, ...]
    coordinates: tuple[Coordinate, ...]
    sites: int = 0

    def text(self) -> str:
        where = ", ".join(c.text() for c in self.coordinates) or "no coordinates in the build files"
        return f"{self.provider} ({where}; apps {', '.join(self.apps)})"

    def to_json(self) -> dict:
        return {"provider": self.provider, "apps": list(self.apps), "sites": self.sites,
                "coordinates": [{"artifact": c.artifact, "version": c.version, "pins": dict(c.pins)} for c in self.coordinates]}


@dataclass(frozen=True)
class Suggestion:
    """One missing provider's coordinate against the catalog: entry when a row matched, reason when it is not used."""
    provider: str
    artifact: str | None
    version: str | None
    apps: tuple[str, ...]
    entry: dict | None = None
    notes: str | None = None
    reason: str | None = None
    applied: bool = False

    def to_json(self) -> dict:
        return {k: list(v) if isinstance(v, tuple) else v for k, v in asdict(self).items() if v is not None}


@dataclass(frozen=True)
class Suggestions:
    missing: tuple[MissingProvider, ...]
    matched: tuple[Suggestion, ...] = field(default_factory=tuple)
    blocked: tuple[Suggestion, ...] = field(default_factory=tuple)
    unmatched: tuple[Suggestion, ...] = field(default_factory=tuple)

    @property
    def applied(self) -> tuple[Suggestion, ...]:
        return tuple(s for s in self.matched if s.applied)

    def left(self) -> tuple[MissingProvider, ...]:
        """The missing providers no applied row covers."""
        covered = {s.provider for s in self.applied}
        return tuple(m for m in self.missing if m.provider not in covered)

    def counts(self) -> dict[str, int]:
        return {"missing": len(self.missing), "matched": len(self.matched), "blocked": len(self.blocked),
                "unmatched": len(self.unmatched), "applied": len(self.applied)}

    def to_json(self, from_apps: str, catalog: str) -> dict:
        return {"schemaVersion": SCHEMA_VERSION, "fromApps": from_apps, "catalog": catalog, "counts": self.counts(),
                "missing": [m.to_json() for m in self.missing],
                **{k: [s.to_json() for s in getattr(self, k)] for k in ("matched", "blocked", "unmatched")}}


def applied_entries(doc: dict | None) -> list[dict]:
    """The providers.bundled entries a bundled-suggestions.yaml applied."""
    return [s["entry"] for s in (doc or {}).get("matched") or [] if s.get("applied")]


def entries_digest(entries: list[dict]) -> str | None:
    """None when nothing is applied, so a run without apply records nothing."""
    return hashlib.sha256(json.dumps(entries, sort_keys=True).encode()).hexdigest() if entries else None
