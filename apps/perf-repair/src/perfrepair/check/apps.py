"""Each app's files the replay checks: dossiers.json against its scopes, units, the groups and the app's screen verdicts;
replacements.json against its dossiers; edits.json against its scopes; harness.yaml against its edits."""
from __future__ import annotations

from pathlib import Path

from .. import run_dir as rd
from ..ai.repair.upgrade.kind import UpgradeKind
from ..ai.runtime.engine.kind import project, rebuild_problems
from ..ai.runtime.engine.outbox import active_outbox
from ..ai.suggest.site_replace.command import site_kind
from ..dto.replacement import read_replacements
from ..dto.screen import Verdict
from ..dto.site import Scope
from ..dto.unit import read_units
from ..files import read_json, read_yaml
from ..review.stability import StabilityKind
from ..run_dir import AppPaths
from ..screen.catalog import Catalog
from ..validation.dossiers.against_run import validate_dossiers
from ..validation.dossiers.parse import parse_dossiers
from ..validation.dossiers.units import validate_dossier_units
from ..validation.replacements import consistent_units, validate_replacements
from ..validation.repair import validate_edits, validate_harness
from .device import parsed


def check_dossiers(run: Path, groups: dict, screen: dict[int, Verdict] | None, catalog: Catalog) -> dict[str, list[str]]:
    out, handler = {}, catalog.handler()
    for directory in sorted(run.glob(f"*/{rd.DOSSIERS}")):
        scopes = [Scope.from_json(s) for s in rd.read_scopes(directory.parent / rd.SCOPES)["scopes"]]
        verdicts = handler.app_verdicts(groups, screen, read_json(directory.parent / rd.APP).get("targetSdk"))
        doc = read_json(directory)
        units = read_units(read_json(directory.parent / rd.UNITS))
        out[str(directory.relative_to(run))] = (validate_dossiers(doc, scopes, groups, verdicts)
                                                + validate_dossier_units(doc, units, scopes, groups))
    return out


def _rebuilt(kind, folder: Path) -> list[str]:
    """The outbox against its files; a folder with no outbox has nothing to rebuild from."""
    outbox = active_outbox(folder)
    return [] if outbox.fingerprint is None else rebuild_problems(kind, outbox.records())


def _replacements(paths: AppPaths, app: str) -> list[str]:
    doc = read_json(paths.replacements)
    units, no_options, problems = parse_dossiers(rd.read_dossiers(paths.dossiers), app)
    replacements = read_replacements(doc)
    return problems + validate_replacements(replacements, doc["sources"], [d for u in units for d in u.dossiers], no_options,
                                            set(doc["stale"])) + consistent_units(replacements, units) + _rebuilt(
        site_kind(paths.root.parent, app), paths.replace)


def _upgrades(paths: AppPaths, app: str) -> list[str]:
    kind = UpgradeKind(app, rd.read_dossiers(paths.dossiers), paths.root)
    records = active_outbox(paths.upgrade).records()
    return kind.validate(project(kind, records), records) + _rebuilt(kind, paths.upgrade)


def _edits(paths: AppPaths, app: str) -> list[str]:
    return validate_edits(read_json(paths.edits), app, {s["id"] for s in rd.read_scopes(paths.scopes)["scopes"]})


def _harness(paths: AppPaths, app: str) -> list[str]:
    return validate_harness(read_yaml(paths.harness), app, paths.root, rd.read_edits(paths.edits))


def check_repair(run: Path) -> dict[str, list[str]]:
    out = {}
    for directory in rd.app_dirs(run):
        paths = AppPaths(run, directory.name)
        for name, file, check in ((rd.REPLACEMENTS, paths.replacements, _replacements), (rd.UPGRADES, paths.upgrades, _upgrades),
                                  (rd.EDITS, paths.edits, _edits),
                                  (rd.HARNESS, paths.harness, _harness)):
            if file.is_file():
                found = parsed(lambda _: check(paths, directory.name), run)
                out[f"{directory.name}/{name}"] = [found] if isinstance(found, str) else found
    return out


def check_stability(run: Path) -> dict[str, list[str]]:
    """review/stability.json against the rebuild of its outbox; its own sample and asks draw the same units."""
    path = rd.review_stability(run)
    if not path.is_file():
        return {}
    def check(_):
        doc = read_json(path)
        kind = StabilityKind(run, doc["sample"], doc["asks"])
        return _rebuilt(kind, rd.review_stability_folder(run))
    found = parsed(check, run)
    return {f"{rd.REVIEW}/{path.name}": [found] if isinstance(found, str) else found}
