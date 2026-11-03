"""The dossier step: scopes + groups + measurements → <app>/dossiers.json, validated before writing."""
from __future__ import annotations

from collections import Counter
from pathlib import Path

from .. import run_dir as rd
from ..catalog.bundled_providers import BundledCatalog
from ..catalog.names import NamesError
from ..catalog.types import types
from ..data_handler.inbound import RunContext
from ..dto.change import DROP_IN
from ..dto.grouping import read_items
from ..dto.shipped import shipped_names
from ..dto.perf_mode import NO_EVIDENCE, PerfMode
from ..dto.site import Scope, reason_code
from ..dto.unit import read_units
from ..files import read_json, write_json
from ..log import step
from ..run_dir import GroupingPaths
from ..screen.catalog import Catalog
from ..validation.grouping.output import read_groups
from ..result.candidates import Family
from ..result.dossier import available_providers, build_dossiers
from ..result.provider_path import SiteProviders, site_providers
from ..result.unit_dossiers import by_unit
from ..validation import require, validate_measurements
from ..validation.dossier_units import validate_dossier_units
from ..validation.dossiers import validate_dossiers


def _canonical(catalog: Catalog, engine_type: str, name: str) -> str | None:
    try:
        found = catalog.names.canonical(engine_type, name)
    except NamesError:
        return None
    return found.name if found.known else None


def _available(run: Path, facts: dict) -> tuple[set[str] | None, frozenset[str], SiteProviders | None]:
    """The providers in the app's process, those of them the app ships, and the provider each site is on; without a
    manifest (None, its names, None)."""
    named = frozenset(shipped_names(facts))
    if not (Path(run) / rd.MANIFEST).is_file():
        return None, named, None
    probe = RunContext.load(Path(run) / rd.MANIFEST).probe
    available = available_providers(probe.platform_providers(), probe.harness_artifacts(), facts)
    on = site_providers(probe.harness_artifacts(), facts, BundledCatalog.load())
    return available, frozenset(available - probe.platform_providers()) | named, on


def family(grouping: GroupingPaths, catalog: Catalog, facts: dict, max_change: str, bundled: frozenset[str]) -> Family:
    """Each item's family from items.json, its canonical name from screen.json, else the names catalog."""
    screen = rd.load_screen(grouping) or {}
    family_of, canonical_of = {}, {}
    for i in read_items(read_json(grouping.items)):
        q = i.qualified
        family_of[q] = i.family
        canonical_of[q] = screen[i.id].canonical if i.id in screen else _canonical(catalog, i.type, i.name)
    return Family(family_of, canonical_of, types(), facts.get("minSdk"), bundled, max_change)


def dossier(run: Path, app: str, source: Path, catalog: Catalog, perf: PerfMode, echo=print,
            max_change: str = DROP_IN) -> dict:
    """max_change: apps.maxChange; the classes above it are recorded in notOffered, never offered."""
    rows, measurements = rd.load_rows(run), rd.load_measurements(run)
    require(rd.MEASUREMENTS, validate_measurements(measurements, rows))
    grouping = GroupingPaths(run)
    catalog.require_same(rd.load_screen_catalog(grouping))
    groups = read_groups(grouping)
    paths = rd.AppPaths(run, app)
    scopes = [Scope.from_json(s) for s in rd.read_scopes(paths.scopes)["scopes"]]
    units = read_units(read_json(paths.units))
    facts = read_json(paths.facts)
    verdicts = catalog.handler().app_verdicts(groups, rd.load_screen(grouping), facts.get("targetSdk"))
    available, shipped, on = _available(run, facts)
    with step("repair", "dossier", app=app) as s:
        doc = by_unit(build_dossiers(app, scopes, facts, groups, rows, measurements.byRow, source, verdicts, perf,
                                    family(grouping, catalog, facts, max_change, shipped), available, on), units,
                     scopes, groups)
        require(rd.DOSSIERS, validate_dossiers(doc, scopes, groups, verdicts) + validate_dossier_units(doc, units, scopes, groups))
        write_json(paths.dossiers, doc)
        s.count(scopes=len(scopes), units=len(doc["units"]), dossiers=len(doc["dossiers"]), options=sum(len(d["options"]) for d in doc["dossiers"]),
                noOptions=dict(Counter(n["reason"] for n in doc["noOptions"])),
                noEvidence=sum(reason_code(n["reason"]) == NO_EVIDENCE for n in doc["noOptions"]),
                byChange=dict(Counter(o.get("change", DROP_IN) for d in doc["dossiers"] for o in d["options"])),
                byTrack=dict(Counter(o["track"] for d in doc["dossiers"] for o in d["options"])),
                needsReview=dict(Counter(r for d in doc["dossiers"] for o in d["options"] for r in o["needsReview"])),
                notOffered=dict(Counter(n["change"] for n in doc["notOffered"])))
        s.wrote(paths.dossiers)
    echo(f"{app}: {len(doc['dossiers'])} dossiers, {len(doc['noOptions'])} scopes without options")
    return doc
