"""Service and alias index over discovery's probe_<utc>.yaml.

The manifest carries the providers and their precedence but not what each registers; app_source
needs that to know which engine types to look for and what an algorithm name canonically is.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

import yaml

SUPPORTED_SCHEMA = 1


@dataclass
class ProbeIndex:
    # (provider, type, NAME-OR-ALIAS upper) -> the provider's registered algorithm name
    names: dict[tuple[str, str, str], str] = field(default_factory=dict)

    @property
    def engine_types(self) -> set[str]:
        return {t for (_, t, _) in self.names}

    def canonical(self, provider: str, engine_type: str, algorithm: str) -> str | None:
        """The provider's own name for `algorithm`, or None when it does not register it.

        JCA matches names case-insensitively, so this does too."""
        return self.names.get((provider, engine_type, algorithm.upper()))


def read_probe_index(path: Path) -> ProbeIndex:
    doc = yaml.safe_load(Path(path).read_text()) or {}
    if doc.get("schemaVersion") != SUPPORTED_SCHEMA:
        raise ValueError(f"{path}: probe schemaVersion {doc.get('schemaVersion')} is not {SUPPORTED_SCHEMA}")
    names: dict[tuple[str, str, str], str] = {}
    for p in doc.get("providers") or []:
        for s in p.get("services") or []:
            for n in [s["algorithm"], *(s.get("aliases") or [])]:
                names.setdefault((p["name"], s["type"], str(n).upper()), s["algorithm"])
    return ProbeIndex(names)
