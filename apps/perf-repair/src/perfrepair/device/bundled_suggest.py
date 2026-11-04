"""The missing set against the bundled-providers catalog: each coordinate matched to its row at the apps' pinned version,
blocked by the row, or unmatched with a reason; never guessed."""
from __future__ import annotations

from dataclasses import replace

from ..catalog.bundled_providers import BundledCatalog
from ..dto.version import newest
from ..dto.bundled import (NAME_TAKEN, NO_CATALOG_ROW, NO_COORDINATES, NO_PINNED_VERSION, Coordinate, MissingProvider,
                           Suggestion, Suggestions)

MATCHED, BLOCKED, UNMATCHED = "matched", "blocked", "unmatched"


def _one(missing: MissingProvider, c: Coordinate, catalog: BundledCatalog, taken: set[str],
         apply: bool) -> tuple[str, Suggestion]:
    row = catalog.rows.get(c.artifact)
    base = Suggestion(missing.provider, c.artifact, c.version, c.apps)
    if row is None or row.provider != missing.provider:
        return UNMATCHED, replace(base, reason=NO_CATALOG_ROW)
    base = replace(base, notes=row.notes)
    if row.blocked:
        return BLOCKED, replace(base, reason=row.blocked)
    if c.version is None:
        return UNMATCHED, replace(base, reason=NO_PINNED_VERSION)
    version = newest(v for _, v in c.pins if v not in row.badVersions)
    if version is None:
        return BLOCKED, replace(base, reason=f"every pin is a known bad version: {', '.join(row.badVersions)}")
    base = replace(base, version=version)
    # two rows registering one name cannot both be installed: the first wins
    name = row.alias or row.provider
    if name in taken:
        return UNMATCHED, replace(base, reason=NAME_TAKEN)
    taken.add(name)
    return MATCHED, replace(base, entry=row.entry(version), applied=apply)


def suggest(missing: list[MissingProvider], catalog: BundledCatalog, apply: bool) -> Suggestions:
    taken: set[str] = set()
    out: dict[str, list[Suggestion]] = {MATCHED: [], BLOCKED: [], UNMATCHED: []}
    for m in missing:
        if not m.coordinates:
            out[UNMATCHED].append(Suggestion(m.provider, None, None, m.apps, reason=NO_COORDINATES))
        for c in m.coordinates:
            kind, suggestion = _one(m, c, catalog, taken, apply)
            out[kind].append(suggestion)
    return Suggestions(tuple(missing), tuple(out[MATCHED]), tuple(out[BLOCKED]), tuple(out[UNMATCHED]))
