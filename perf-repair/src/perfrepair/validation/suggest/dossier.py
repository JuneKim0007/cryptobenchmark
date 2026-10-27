"""dossiers.json: its header, and each dossier whole enough to ask about."""
from __future__ import annotations

from ...dto.grouping import parse_qualified
from ...dto.site import KEY_SOURCES, METRICS, SCHEMA_VERSION, SINKS, Dossier, scope_id


def provider_of(item: str) -> str:
    return parse_qualified(item)[2]


def validate_dossier(d: Dossier, app: str) -> list[str]:
    s, k = d.scope, d.key
    problems = [p for p in (
        f"{k}: scope app {s.app!r} is not {app!r}" if s.app != app else "",
        f"{k}: id is not the scope_id of its site" if s.id != scope_id(s.app, s.file, s.function, s.line, s.call) else "",
        f"{k}: sinks {list(s.sinks)} outside {SINKS}" if set(s.sinks) - set(SINKS) else "",
        f"{k}: key source {s.keySource!r} is not one of {KEY_SOURCES}" if s.keySource not in KEY_SOURCES else "",
        f"{k}: line {s.line} is outside the function span {s.start}..{s.end}" if not s.start <= s.line <= s.end else "",
        f"{k}: source is empty" if not d.source.strip() else "",
    ) if p]
    items = [d.current] + [o.item for o in d.options]
    for item in items:
        try:
            provider_of(item)
        except ValueError:
            problems.append(f"{k}: {item!r} is not a qualified item id")
    aliases = [o.alias for o in d.options]
    if len(set(aliases)) != len(aliases) or not all(aliases):
        problems.append(f"{k}: option aliases {aliases} are not unique and non-empty")
    if len(set(items)) != len(items):
        problems.append(f"{k}: an option repeats the current item or another option")
    for o in d.options:
        for e in o.estimates:
            if e.metric not in METRICS:
                problems.append(f"{k}: {o.alias} estimate metric {e.metric!r} is not one of {METRICS}")
            if not 0.0 <= e.pImprove <= 1.0 or e.ratio <= 0 or e.n < 1:
                problems.append(f"{k}: {o.alias} {e.metric} estimate out of range (ratio {e.ratio}, "
                                f"pImprove {e.pImprove}, n {e.n})")
    return problems


def parse_dossiers(doc: dict, app: str) -> tuple[list[Dossier], list[str]]:
    if doc.get("schemaVersion") != SCHEMA_VERSION:
        return [], [f"dossiers schemaVersion {doc.get('schemaVersion')} is not {SCHEMA_VERSION}"]
    if doc.get("app") != app:
        return [], [f"dossiers are for app {doc.get('app')!r}, not {app!r}"]
    dossiers, problems = [], []
    for i, raw in enumerate(doc.get("dossiers") or []):
        try:
            d = Dossier.from_json(raw)
        except (KeyError, TypeError, ValueError) as e:
            problems.append(f"dossiers[{i}]: does not parse into Dossier: {e!r}")
            continue
        problems += validate_dossier(d, app)
        dossiers.append(d)
    keys = [d.key for d in dossiers]
    problems += [f"{k}: scope appears more than once" for k in sorted({k for k in keys if keys.count(k) > 1})]
    return dossiers, problems
