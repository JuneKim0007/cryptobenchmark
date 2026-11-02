"""python3 -m perfrepair.repair — scopes → dossiers → test set; replacements → edits → harness."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import yaml

from ..app.facts.path_id import absolute, app_id
from ..dto.site import Replacement, Scope, read_replacements
from ..files import read_json, write_json, write_text
from .. import run_dir as rd
from ..run_dir import AppPaths
from ..config.args import add_config_arg, load_settings
from ..config.device_results import add_device_results_arg, fill_device_results
from ..log import log_to_stderr
from ..failure import reported
from ..screen.catalog import screening_catalog
from ..validation.repair import validate_edits, validate_harness
from .dossier import dossier
from .edit import edit_app, load_specs
from .harness import harness
from .inputs import read_effective
from .test_set import build_test_set


def main(argv: list[str] | None = None) -> int:
    log_to_stderr()
    ap = argparse.ArgumentParser(prog="perfrepair.repair")
    sub = ap.add_subparsers(dest="command", required=True)
    for name in ("dossier", "test-set", "edit", "harness"):
        p = sub.add_parser(name)
        add_device_results_arg(p)
        add_config_arg(p)
        p.add_argument("--app", type=Path, required=True,
                       help="the app's source root, only read; its path gives the app's id, scope files are relative to it")
    sub.choices["test-set"].add_argument("-o", "--out", type=Path, required=True)
    a = ap.parse_args(argv)
    return reported(lambda: STEPS[a.command](ap, _located(ap, a)))


def _located(ap: argparse.ArgumentParser, a: argparse.Namespace) -> argparse.Namespace:
    fill_device_results(ap, a)
    a.source, a.app = absolute(a.app), app_id(a.device_results, a.app)
    return a


def _dossier(ap: argparse.ArgumentParser, a: argparse.Namespace) -> None:
    dossier(a.device_results, a.app, a.source, screening_catalog(load_settings(ap, a)))


def _test_set(_ap: argparse.ArgumentParser, a: argparse.Namespace) -> int:
    doc = build_test_set(read_json(AppPaths(a.device_results, a.app).dossiers), a.app)
    write_text(a.out, yaml.safe_dump(doc, sort_keys=False))
    print(f"{a.out}: {len(doc['include'])} primitives")
    return 0


def _load(paths: AppPaths) -> tuple[dict[str, Scope], dict[str, Replacement]]:
    scopes = {s["id"]: Scope.from_json(s) for s in read_json(paths.scopes)["scopes"]}
    replacements = read_replacements(read_json(paths.replacements))
    return scopes, replacements


def _report(path: Path, problems: list[str]) -> int:
    print("\n".join(problems), file=sys.stderr)
    print(f"{path}: not written, {len(problems)} problem(s)", file=sys.stderr)
    return 1


def _edit(_ap: argparse.ArgumentParser, a: argparse.Namespace) -> int:
    paths = AppPaths(a.device_results, a.app)
    scopes, replacements = _load(paths)
    doc = edit_app(scopes, list(replacements.values()), a.source, paths, load_specs())
    problems = validate_edits(doc, a.app, set(scopes))
    if problems:
        return _report(paths.edits, problems)
    write_json(paths.edits, doc)
    applied = sum(e["status"] == "applied" for e in doc["edits"])
    print(f"{paths.edits}: {applied} of {len(doc['edits'])} replacements applied")
    return 0


def _harness(_ap: argparse.ArgumentParser, a: argparse.Namespace) -> int:
    paths = AppPaths(a.device_results, a.app)
    scopes, replacements = _load(paths)
    edits = read_json(paths.edits)
    currents = {d["scope"]["id"]: d["current"] for d in read_json(paths.dossiers)["dossiers"]}
    doc = harness(paths, scopes, replacements, edits, currents, read_effective(a.device_results / rd.MANIFEST))
    problems = validate_harness(doc, a.app, paths.root, edits)
    if problems:
        return _report(paths.harness, problems)
    write_text(paths.harness, yaml.safe_dump(doc, sort_keys=False))
    print(f"{paths.harness}: {len(doc['scopes'])} scopes")
    return 0


STEPS = {"dossier": _dossier, "test-set": _test_set, "edit": _edit, "harness": _harness}


if __name__ == "__main__":
    sys.exit(main())
