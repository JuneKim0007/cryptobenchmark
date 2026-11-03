"""device.bundled.fromApps apply: the base config's providers.bundled, the entries the last suggestions applied, and
bundled-global.yaml, the base with them appended; with none applied the base is used as it is. The per-app harness builds
the same entries, or a candidate from an applied provider would not exist in it."""
from __future__ import annotations

from pathlib import Path

from .. import run_dir as rd
from ..dto.bundled import applied_entries
from ..files import read_yaml
from .selection import generated, relocated


def configured(base: Path) -> frozenset[str]:
    """The group:name of each providers.bundled entry the base config holds."""
    entries = ((read_yaml(base) or {}).get("providers") or {}).get("bundled") or []
    return frozenset(e["artifact"].rsplit(":", 1)[0] for e in entries if isinstance(e, dict) and e.get("artifact"))


def last_applied(folder: Path) -> list[dict]:
    path = Path(folder) / rd.BUNDLED_SUGGESTIONS
    return applied_entries(read_yaml(path)) if path.is_file() else []


def harness_config(device: Path, chosen: Path | None, app_folder: Path) -> Path | None:
    """chosen: apps.benchmarkConfig; unset, the device stage's own bundled-global.yaml already holds the entries."""
    made = Path(device) / rd.BUNDLED_CONFIG
    if not made.is_file():
        return chosen
    return bundled_config(chosen, app_folder, last_applied(device)) if chosen else made


def bundled_config(base: Path, folder: Path, entries: list[dict]) -> Path:
    path = Path(folder) / rd.BUNDLED_CONFIG
    if not entries:
        path.unlink(missing_ok=True)
        return Path(base)
    document = relocated(base)
    providers = dict(document.get("providers") or {})
    providers["bundled"] = list(providers.get("bundled") or []) + entries
    path.parent.mkdir(parents=True, exist_ok=True)
    return generated(path, base, "device.bundled.fromApps apply", {**document, "providers": providers})
