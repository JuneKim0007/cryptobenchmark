"""The rows of primitives_missing.yaml, one function per place a primitive an app uses is found unavailable."""
from __future__ import annotations

from collections import Counter
from pathlib import Path

from .. import run_dir as rd
from ..dto.bundled import APPLY, BundledPolicy, Suggestions
from ..dto.dossier import (
    NOT_ON_DEVICE,
    NOT_ON_DEVICE_ABSENT,
    NOT_ON_DEVICE_STEP,
    VARIANT_NOT_MEASURED,
    not_on_device_sites,
)
from ..dto.grouping import parse_qualified, qualified, read_items
from ..dto.primitives_missing import (
    ABSENT_ON_DEVICE,
    BUNDLED_MISSING,
    HOST_CANNOT_BUILD,
    NO_DEVICE_ITEM,
    NOT_MEASURED,
    NOT_SCREENED,
    SKIPPED,
    STOPPED,
    MissingRow,
)
from ..dto.run_log import RunLog
from ..dto.shipped import shipped, shipped_names
from ..files import read_json
from ..run_dir import AppPaths, GroupingPaths, read_sites
from ..stop import CODES
from ..stop.codes import STOP
from ..stop.policy import action

ONLY_DEVICE_BUILDS = "only a --device run builds and installs bundled providers"
HOST_NEXT = f"a host cannot build it: {ONLY_DEVICE_BUILDS}; run the guide with --device"
NO_ITEM_NEXT = "the run has no item for it: add it to the test set, or check the provider registers it"
VARIANT_NEXT = "the benchmark measured it only in the other variant, so this site gets no option; check run.variants and the test set"
RESOLVED = ("default", "explicit")
UNMEASURED_STATUSES = ("skipped", "unmeasured", "not_runnable")


def _action_of(code: str) -> str:
    return STOPPED if action(CODES[code]) == STOP else SKIPPED


def _primitive(engine_type: str, algorithm: str | None) -> str:
    return f"{engine_type} {algorithm}" if algorithm else engine_type


def _sites(device: Path, app: str) -> list[dict]:
    path = AppPaths(device, app).sites
    return read_sites(path)["sites"] if path.is_file() else []


def _facts(device: Path, app: str) -> dict:
    path = AppPaths(device, app).facts
    return read_json(path) if path.is_file() else {}


def _coordinates(facts: dict, provider: str | None) -> tuple[str, ...]:
    return tuple(sorted(f"{s.artifact}:{s.version}" if s.version else s.artifact
                        for s in shipped(facts) if provider and s.providerName == provider))


def _algorithm(site: dict) -> str | None:
    return site.get("canonicalAlgorithm") or site.get("resolvedAlgorithm")


def _name(site: dict) -> str:
    return qualified(site["engineType"], site["resolvedAlgorithm"], site["resolvedProvider"])


def _resolved(sites: list[dict]) -> list[dict]:
    return [s for s in sites if s.get("resolvedProvider") and s.get("resolvedAlgorithm")]


def _rows(sites: list[dict], app: str, facts: dict, reason: str, how: str, step) -> list[MissingRow]:
    """One row per primitive and provider; step: the next step, or per site what it is."""
    counts = Counter((s["engineType"], _algorithm(s), s.get("resolvedProvider")) for s in sites)
    first = {}
    for s in sites:
        first.setdefault((s["engineType"], _algorithm(s), s.get("resolvedProvider")), s)
    return [MissingRow(_primitive(engine, algorithm), provider, reason, (app,), n, how, _coordinates(facts, provider),
                       step(first[engine, algorithm, provider]) if callable(step) else step)
            for (engine, algorithm, provider), n in counts.items()]


def _no_item_rows(device: Path, app: str, sites: list[dict], facts: dict) -> list[MissingRow]:
    items = GroupingPaths(device).items
    if not items.is_file():
        return []
    held = {i.qualified for i in read_items(read_json(items))}
    lost = [s for s in _resolved(sites) if s["resolution"] in RESOLVED and _name(s) not in held]
    return _rows(lost, app, facts, NO_DEVICE_ITEM, SKIPPED, NO_ITEM_NEXT)


def site_rows(device: Path, app: str) -> list[MissingRow]:
    """not_on_device, the absent form the app step only prints, and a site on a device provider no item holds."""
    sites, facts = _sites(device, app), _facts(device, app)
    absent = {m for m, _, gone in not_on_device_sites(sites, shipped_names(facts)) if gone}
    gone = [s for s in sites if s["resolution"] == NOT_ON_DEVICE]
    return [*_rows([s for s in gone if s["missing"] in absent], app, facts, ABSENT_ON_DEVICE, SKIPPED, NOT_ON_DEVICE_ABSENT),
            *_rows([s for s in gone if s["missing"] not in absent], app, facts, NOT_ON_DEVICE, _action_of(NOT_ON_DEVICE),
                   NOT_ON_DEVICE_STEP),
            *_no_item_rows(device, app, sites, facts)]


def bundled_rows(found: Suggestions, policy: BundledPolicy, on_device: bool, configured: frozenset[str]) -> list[MissingRow]:
    """Each provider no applied row covers; a host's matched or configured one says the host cannot build it."""
    how = _action_of(BUNDLED_MISSING)
    verdicts = {s.provider: s for s in (*found.matched, *found.unmatched, *found.blocked)}
    matched = {s.provider for s in found.matched} if policy.fromApps == APPLY else set()
    rows = []
    for m in found.left():
        said = verdicts.get(m.provider)
        built = m.provider in matched or any(c.artifact in configured for c in m.coordinates)
        host = built and not on_device
        why = f"{said.reason}; " if said and said.reason else ""
        step = HOST_NEXT if host else why + CODES[BUNDLED_MISSING].next
        rows.append(MissingRow(None, m.provider, HOST_CANNOT_BUILD if host else BUNDLED_MISSING, m.apps, m.sites, how,
                               tuple(c.text() for c in m.coordinates), step))
    return rows


def not_screened_rows(device: Path, names: tuple[str, ...], apps: list[str]) -> list[MissingRow]:
    """Every name the benchmark measured with no verdict, with the apps whose sites resolve to it."""
    used: dict[str, Counter] = {}
    for app in apps:
        for s in _resolved(_sites(device, app)):
            used.setdefault(_name(s), Counter())[app] += 1
    rows = []
    for name in names:
        engine, algorithm, provider = parse_qualified(name)
        by_app = used.get(name, Counter())
        rows.append(MissingRow(_primitive(engine, algorithm), provider, NOT_SCREENED, tuple(sorted(by_app)),
                               sum(by_app.values()), STOPPED, (), CODES["primitive_not_screened"].next))
    return rows


def measured_rows(device: Path, app: str) -> list[MissingRow]:
    """A site's item the run log says was never measured: skipped, not runnable, or planned with no samples."""
    path = Path(device) / rd.RUN_LOG
    if not path.is_file():
        return []
    entries = RunLog.from_json(read_json(path)).entries
    done = {qualified(e.type, e.algorithm, e.provider) for e in entries if e.status == "measured"}
    lost = {qualified(e.type, e.algorithm, e.provider): e.reason or e.status for e in entries
            if e.status in UNMEASURED_STATUSES and e.type and e.algorithm and e.provider}
    sites = [s for s in _resolved(_sites(device, app)) if _name(s) in lost and _name(s) not in done]
    return _rows(sites, app, _facts(device, app), NOT_MEASURED, SKIPPED,
                 lambda s: f"the benchmark did not measure it: {lost[_name(s)]}")


def variant_rows(device: Path, app: str, no_options: list[dict]) -> list[MissingRow]:
    """A scope whose primitive was measured only in the other benchmark variant, so it gets no option."""
    ids = {n["scope"] for n in no_options if n["reason"] == VARIANT_NOT_MEASURED}
    if not ids:
        return []
    scopes = rd.read_scopes(AppPaths(device, app).scopes)["scopes"]
    named = Counter((s["engineType"], s.get("algorithm"), s.get("provider")) for s in scopes if s["id"] in ids)
    return [MissingRow(_primitive(engine, algorithm), provider, VARIANT_NOT_MEASURED, (app,), n, SKIPPED, (), VARIANT_NEXT)
            for (engine, algorithm, provider), n in named.items()]
