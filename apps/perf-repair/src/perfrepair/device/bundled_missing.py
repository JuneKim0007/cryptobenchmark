"""The missing set: the JCA providers the target apps ship (app.json `bundled`) or name at a site that resolved
not_on_device, that neither the device's own providers nor the base config's providers.bundled hold."""
from __future__ import annotations

from collections import Counter
from pathlib import Path

from ..dto.bundled import Coordinate, MissingProvider
from ..dto.dossier import NOT_ON_DEVICE
from ..dto.shipped import shipped as app_shipped
from ..files import read_json
from ..run_dir import AppPaths, read_sites


def _app_needs(device: Path, app: str) -> tuple[dict[str, list[tuple[str, str | None]]], Counter]:
    """Per provider name the app ships: its (artifact, pinned version); and per provider its not_on_device sites."""
    paths = AppPaths(device, app)
    shipped: dict[str, list[tuple[str, str | None]]] = {}
    facts = read_json(paths.facts) if paths.facts.is_file() else {}
    for s in app_shipped(facts):
        if s.providerName:
            shipped.setdefault(s.providerName, []).append((s.artifact, s.version))
    sites = read_sites(paths.sites)["sites"] if paths.sites.is_file() else []
    # an explicit provider not on the device resolves to its own name; a default site's missing is a service
    named = Counter(s["resolvedProvider"] for s in sites if s["resolution"] == NOT_ON_DEVICE and s.get("resolvedProvider"))
    return shipped, named


def missing_set(device: Path, apps: list[str], platform: frozenset[str], configured: frozenset[str]) -> list[MissingProvider]:
    """platform: the names the device registers itself; configured: the group:name of each base providers.bundled entry."""
    pins: dict[str, dict[str, list[tuple[str, str | None]]]] = {}
    sites: Counter = Counter()
    users: dict[str, set[str]] = {}
    for app in apps:
        shipped, named = _app_needs(device, app)
        sites.update(named)
        for provider, found in shipped.items():
            for artifact, version in found:
                pins.setdefault(provider, {}).setdefault(artifact, []).append((app, version))
        for provider in {*shipped, *named}:
            users.setdefault(provider, set()).add(app)
    out = []
    for provider in sorted(users):
        coordinates = pins.get(provider, {})
        if provider in platform or any(artifact in configured for artifact in coordinates):
            continue
        out.append(MissingProvider(provider, tuple(sorted(users[provider])),
                                   tuple(Coordinate(a, tuple(sorted(p))) for a, p in sorted(coordinates.items())),
                                   sites[provider]))
    return out
