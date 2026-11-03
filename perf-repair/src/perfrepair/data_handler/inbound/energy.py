"""The energy cases a run marked invalid, from each energy.json its manifest lists (one per process repetition)."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from ...files import read_json, read_yaml

ENERGY_KEY = "energy"


@dataclass(frozen=True)
class InvalidCase:
    case: str
    reasons: tuple[str, ...]
    file: Path


def energy_files(manifest: Path) -> list[Path]:
    # only files.energy: a --harness manifest is no device manifest, so the whole schema is not read
    base, listed = Path(manifest).parent, (read_yaml(manifest).get("files") or {}).get(ENERGY_KEY) or []
    return [(base / rel).resolve() for rel in ([listed] if isinstance(listed, str) else listed)]


def invalid_cases(manifest: Path) -> list[InvalidCase]:
    """A listed file that is missing holds no case; the run that wrote the manifest reported it."""
    out = []
    for path in (p for p in energy_files(manifest) if p.is_file()):
        for case, row in (read_json(path).get("cases") or {}).items():
            if row.get("valid") is False:
                out.append(InvalidCase(case, tuple(row.get("invalid") or ()), path))
    return out
