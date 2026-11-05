"""Scopes + groups + measurements → one Dossier per scope with options, or the reason it has none."""
from __future__ import annotations

from collections import defaultdict
from pathlib import Path

from ..dto import PrimitiveRow, Summary
from ..dto.grouping import provider_of, qualified
from ..dto.screen import Verdict
from ..dto.lifecycle import NO_REAL_USE as NO_REAL_USE_STATUS
from ..dto.perf_mode import PerfMode
from ..dto.site import DOSSIERS_SCHEMA_VERSION, Scope
from ..dto.dossier import BROKEN_USE, NO_REAL_USE, NOT_ON_DEVICE, VARIANT_NOT_MEASURED, Dossier
from ..dto.pattern import VARIANTS
from ..dto.shipped import shipped, shipped_names
from ..dto.change import DROP_IN
from ..dto.upgrade import UpgradeItem
from .candidates import Family
from .configurations import Config, config_of
from .options import Joined
from .provider_path import SiteProviders
from ..stop.halt import Coded

RESOLVED = ("default", "explicit")


def function_source(root: Path, scope: Scope) -> str:
    lines = (Path(root) / scope.file).read_text(errors="replace").splitlines()
    return "\n".join(lines[scope.start - 1:scope.end])


def _unresolved(s: Scope, named: bool = False) -> str | None:
    """named: the site names a provider the app ships, which the run measures under another name."""
    if s.lifecycle is not None and s.lifecycle.status == NO_REAL_USE_STATUS:
        return NO_REAL_USE
    if s.resolution == NOT_ON_DEVICE and not named:
        return NOT_ON_DEVICE
    resolved = s.resolution in RESOLVED or named
    return None if resolved and s.algorithm is not None and s.provider is not None else "unresolved"


def available_providers(platform: frozenset[str], harness: dict[str, str], app_doc: dict) -> set[str]:
    """What the app's process has: the device's own and what the app ships; harness: per provider providers.bundled
    installed, its group:name, the same library under the harness's own name counting as shipped."""
    artifacts = {s.artifact for s in shipped(app_doc)}
    return {*platform, *shipped_names(app_doc), *(p for p, artifact in harness.items() if artifact in artifacts)}


Measured = dict[str, dict[Config, PrimitiveRow]]


def _measured(rows: list[PrimitiveRow]) -> dict[str, Measured]:
    """Per benchmark variant, the rows by item: a scope reads only its pattern's, so the two never mix."""
    bare = sorted(r.rowId for r in rows if r.parameters is None)
    if bare:
        raise Coded(f"missing_parameters: rows {', '.join(bare)} report no parameters; the benchmark always writes them")
    measured: dict[str, Measured] = {v: defaultdict(dict) for v in VARIANTS}
    for r in rows:
        measured[r.variant][qualified(r.type, r.algorithm, r.provider)][config_of(r)] = r
    return measured


def _variant_missing(s: Scope, current: str, measured: dict[str, Measured]) -> str | None:
    """The current item measured, but not in the scope's variant (a fixed-only key generation, a legacy run)."""
    others = any(current in m for v, m in measured.items() if v != s.pattern)
    return VARIANT_NOT_MEASURED if others and current not in measured[s.pattern] else None


def _probed_or_shipped(groups: dict, app_doc: dict) -> set[str]:
    return {provider_of(v["qualified"]) for v in groups["items"].values()} | shipped_names(app_doc)


def build_dossiers(app: str, scopes: list[Scope], app_doc: dict, groups: dict, rows: list[PrimitiveRow],
                   measurements: dict[str, dict[str, Summary | None]], source_root: Path,
                   verdicts: dict[str, Verdict] | None, perf: PerfMode, family: Family | None = None,
                   available: set[str] | None = None, providers: SiteProviders | None = None) -> dict:
    """verdicts: each item's screen verdict for this app by qualified name; None without screen.json.
    perf: only its metrics are estimated, and an option without one it requires is dropped.
    family: the type catalog's candidates beyond the group up to its maxChange; None offers drop-ins only.
    available: the providers in the app's process; None, without a probe: every probed one and what the app ships.
    providers: the provider each site is on for this app; None: the scope's own, by order when its resolution is default."""
    if available is None:
        available = _probed_or_shipped(groups, app_doc)
    measured = _measured(rows)
    joined = {v: Joined(groups, m, measurements, verdicts, perf, available, family) for v, m in measured.items()}
    dossiers, none, kept, upgrades, unreached = [], [], [], [], []
    items = {v["qualified"] for v in groups["items"].values()}
    for s in scopes:
        on, by_order = providers.on(s, items) if providers else (s.provider, s.resolution == "default")
        unresolved = _unresolved(s, on != s.provider) or _variant_missing(
            s, qualified(s.engineType, s.algorithm, on or s.provider), measured)
        current, options, reason, others = (None, [], unresolved, []) if unresolved else joined[s.pattern].options(s, on, by_order)
        kept += [{"scope": s.id, **c.to_json()} for c in others]
        item = current or (qualified(s.engineType, s.algorithm, on or s.provider) if s.algorithm and (on or s.provider) else None)
        broken = joined[s.pattern].broken(item)
        if reason is not None:
            none.append({"scope": s.id, "reason": reason})
            unreached += [{"scope": s.id, "current": item, "reason": reason}] * broken
            continue
        per_call = tuple(sorted({r.perCall for r in measured[s.pattern][current].values() if r.perCall}))
        built = Dossier(s, function_source(source_root, s), current, tuple(options), per_call)
        if broken:
            none.append({"scope": s.id, "reason": BROKEN_USE})
            upgrades.append(UpgradeItem(built, joined[s.pattern].identified(current, options),
                                        measured=joined[s.pattern].own_numbers(s, options),
                                        screenReason=verdicts[current].reason).to_json())
        else:
            dossiers.append(built)
    return {"schemaVersion": DOSSIERS_SCHEMA_VERSION, "app": app, "perfMode": perf.to_json(),
            "measured": [m for m in perf.names if any(by_metric.get(m) for by_metric in measurements.values())],
            "maxChange": family.max_change if family else DROP_IN, "dossiers": [d.to_json() for d in dossiers],
            "noOptions": none, "notOffered": kept, "units": [], "upgrades": upgrades, "brokenUnreached": unreached}
