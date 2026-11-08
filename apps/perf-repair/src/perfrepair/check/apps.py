"""Each app's files the replay checks: dossiers.json against its scopes, units, the groups and the app's screen verdicts;
replacements.json against its dossiers; edits.json against its scopes; harness.yaml against its edits."""
from __future__ import annotations

from pathlib import Path

from .. import run_dir as rd
from ..ai.select.replay import replay_problems
from ..ai.select.units import UnitSource
from ..ai.select.upgrades import UpgradeSource
from ..dto.screen import Verdict
from ..dto.site import Scope
from ..dto.unit import read_units
from ..files import read_json, read_yaml
from ..run_dir import AppPaths
from ..screen.catalog import Catalog
from ..validation.dossiers.against_run import validate_dossiers
from ..validation.dossiers.units import validate_dossier_units
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


def _replacements(paths: AppPaths, app: str) -> list[str]:
    return replay_problems(UnitSource(paths.root.parent, app))


def _upgrades(paths: AppPaths, app: str) -> list[str]:
    return replay_problems(UpgradeSource(paths.root.parent, app))


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

