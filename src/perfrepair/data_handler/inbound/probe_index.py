from __future__ import annotations

from ...files import read_yaml

from dataclasses import dataclass, field
from pathlib import Path


SUPPORTED_SCHEMA = 1


@dataclass
class ProbeIndex:
    names: dict[tuple[str, str, str], str] = field(default_factory=dict)

    @property
    def engine_types(self) -> set[str]:
        return {t for (_, t, _) in self.names}

    def canonical(self, provider: str, engine_type: str, algorithm: str) -> str | None:
        return self.names.get((provider, engine_type, algorithm.upper()))


def read_probe_index(path: Path) -> ProbeIndex:
    doc = read_yaml(path)
    if doc.get("schemaVersion") != SUPPORTED_SCHEMA:
        raise ValueError(f"{path}: probe schemaVersion {doc.get('schemaVersion')} is not {SUPPORTED_SCHEMA}")
    names: dict[tuple[str, str, str], str] = {}
    for p in doc.get("providers") or []:
        for s in p.get("services") or []:
            for n in [s["algorithm"], *(s.get("aliases") or [])]:
                names.setdefault((p["name"], s["type"], str(n).upper()), s["algorithm"])
    return ProbeIndex(names)
