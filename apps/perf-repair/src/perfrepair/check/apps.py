"""Each app's files the replay checks: dossiers.json against its scopes, units, the groups and the app's screen verdicts;
replacements.json against its dossiers; edits.json against its scopes; harness.yaml against its edits."""
from __future__ import annotations

from pathlib import Path

from cryptobench.paths import AppTree, RunTree
from cryptobench.paths import DOSSIERS, EDITS, HARNESS, REPLACEMENTS, UPGRADES
from .. import run_dir as rd
from ..ai.select.replay import replay_problems
from ..ai.select.units import UnitSource
from ..ai.select.upgrades import UpgradeSource
from ..dto.screen import Verdict
from ..dto.site import Scope
from ..dto.unit import read_units
from ..files import read_json, read_yaml
from ..screen.catalog import Catalog
from ..validation.dossiers.against_run import validate_dossiers
from ..validation.dossiers.units import validate_dossier_units
from ..validation.repair import validate_edits, validate_harness
from .device import parsed


def check_dossiers(run: Path, groups: dict, screen: dict[int, Verdict] | None, catalog: Catalog) -> dict[str, list[str]]:
    out, handler = {}, catalog.handler()
    for directory in sorted(run.glob(f"*/{DOSSIERS}")):
        scopes = [Scope.from_json(s) for s in rd.read_scopes(AppTree.at(directory.parent).scopes)["scopes"]]
        verdicts = handler.app_verdicts(groups, screen, read_json(AppTree.at(directory.parent).facts).get("targetSdk"))
        doc = read_json(directory)
        units = read_units(read_json(AppTree.at(directory.parent).units))
        out[str(directory.relative_to(run))] = (validate_dossiers(doc, scopes, groups, verdicts)
                                                + validate_dossier_units(doc, units, scopes, groups))
    return out


def _replacements(paths: AppTree, app: str) -> list[str]:
    return replay_problems(UnitSource(paths.root.parent, app))


def _upgrades(paths: AppTree, app: str) -> list[str]:
    return replay_problems(UpgradeSource(paths.root.parent, app))


def _edits(paths: AppTree, app: str) -> list[str]:
    return validate_edits(read_json(paths.edits), app, {s["id"] for s in rd.read_scopes(paths.scopes)["scopes"]})


def _harness(paths: AppTree, app: str) -> list[str]:
    return validate_harness(read_yaml(paths.harness), app, paths.root, rd.read_edits(paths.edits))


def check_repair(run: Path) -> dict[str, list[str]]:
    out = {}
    for directory in RunTree(run).apps():
        paths = AppTree(run, directory.name)
        for name, file, check in ((REPLACEMENTS, paths.replacements, _replacements), (UPGRADES, paths.upgrades, _upgrades),
                                  (EDITS, paths.edits, _edits),
                                  (HARNESS, paths.harness, _harness)):
            if file.is_file():
                found = parsed(lambda _: check(paths, directory.name), run)
                out[f"{directory.name}/{name}"] = [found] if isinstance(found, str) else found
    return out

