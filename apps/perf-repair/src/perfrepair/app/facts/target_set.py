"""apps.targets → the apps to run and every candidate left out with its reason: root and path entries, inline or from a
targets file, merged by resolved path and then applicationId."""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from cryptobench import paths
from ...files import read_yaml
from ...inputs.check import (
    TARGETS_EXPECTED,
    target_ok,
    target_path,
    target_perf,
    target_root,
)
from ...stop.halt import Coded
from .kind import APP, LIBRARY, Kind, android_kind
from .roots import EscapingLink, project_roots

TARGETS_SCHEMA_VERSION = 1
MISSING = "missing"


@dataclass(frozen=True)
class Target:
    path: Path
    kind: Kind
    entry: dict
    perfMode: Any = None

    def to_json(self) -> dict:
        return {"path": str(self.path), "kind": self.kind.kind, "applicationId": self.kind.applicationId,
                "entry": self.entry, "perfMode": self.perfMode.name if self.perfMode else None}


@dataclass(frozen=True)
class Skipped:
    path: Path
    kind: str
    reason: str
    entry: dict
    # a path entry that is no app is that app's stop; a root's other candidates are only recorded
    stops: bool = False

    def to_json(self) -> dict:
        return {"path": str(self.path), "kind": self.kind, "reason": self.reason, "entry": self.entry}


@dataclass
class TargetSet:
    apps: list[Target] = field(default_factory=list)
    skipped: list[Skipped] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    def document(self) -> dict:
        return {"schemaVersion": TARGETS_SCHEMA_VERSION, "apps": [t.to_json() for t in self.apps],
                "skipped": [s.to_json() for s in self.skipped]}

    def add(self, target: Target) -> None:
        first = next((t for t in self.apps if t.path == target.path or (
            target.kind.applicationId and t.kind.applicationId == target.kind.applicationId)), None)
        if first:
            self.skipped.append(Skipped(target.path, target.kind.kind, f"duplicate_of: {first.path}", target.entry))
        else:
            self.apps.append(target)


def listed_entries(value: Any, settings_file: Path) -> tuple[list, Path]:
    """The entries and the file their relative paths resolve against: perfrepair.yaml, or the targets file."""
    if not isinstance(value, str):
        return list(value or []), Path(settings_file)
    path = paths.against(settings_file, value)
    if not path.is_file():
        raise Coded(f"missing_file: apps.targets file {path}")
    entries = read_yaml(path, list)
    if not all(target_ok(e) for e in entries):
        raise Coded(f"invalid: apps.targets file {path}, {TARGETS_EXPECTED}")
    return entries, path


def _from_root(found: TargetSet, root: Path, perf: Any) -> None:
    entry = {"root": str(root)}
    if not root.is_dir():
        found.skipped.append(Skipped(root, MISSING, "not a folder", entry))
        found.warnings.append(f"apps.targets root {root} is no folder; it holds no app")
        return
    try:
        rels = project_roots(root, manifests=True)
    except EscapingLink as e:
        found.warnings.append(f"apps.targets root {root}: escapes_root: {e}; it holds no app")
        return
    before = len(found.apps)
    for rel in rels:
        path = (root / rel).resolve()
        kind = android_kind(path)
        if kind.kind == APP:
            found.add(Target(path, kind, entry, perf))
        else:
            found.skipped.append(Skipped(path, kind.kind, kind.reason or kind.kind, entry))
    if len(found.apps) == before:
        found.warnings.append(f"apps.targets root {root} holds no app ({len(rels)} candidates, none an app)")


def _from_path(found: TargetSet, path: Path, perf: Any) -> None:
    entry = {"path": str(path)}
    if not path.is_dir():
        found.skipped.append(Skipped(path, MISSING, "not a folder", entry, stops=True))
        return
    kind = android_kind(path)
    if kind.kind in (APP, LIBRARY):
        found.add(Target(path, kind, entry, perf))
    else:
        found.skipped.append(Skipped(path, kind.kind, kind.reason or kind.kind, entry, stops=True))


def resolve_targets(value: Any, settings_file: Path) -> TargetSet:
    """Entries in order; a root's apps in path order; perfMode of the entry that found an app first."""
    entries, base = listed_entries(value, settings_file)
    found = TargetSet()
    for e in entries:
        root = target_root(e)
        folder = paths.against(base, root or target_path(e))
        (_from_root if root else _from_path)(found, folder, target_perf(e))
    return found
