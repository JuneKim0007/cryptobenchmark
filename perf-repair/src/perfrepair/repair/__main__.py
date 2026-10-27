"""python3 -m perfrepair.repair — call sites → test set → replacements → edits → harness → before/after."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import yaml

from .. import run_dir as rd
from ..dto.grouping import parse_qualified
from ..files import read_json, write_json, write_text
from ..grouping.paths import GroupingPaths
from ..ai.evaluate.worthiness.kind import VERDICTS
from ..dto.site import Replacement, Scope
from ..validation.repair import validate_edits, validate_harness
from .candidates import Candidate, candidates
from .choose import choose
from .edit import edit_app
from .edit.specs import load as load_specs
from .harness import harness
from .paths import AppPaths
from .replay import compare, side
from .test_set import build_test_set

DIRECTORY = "repair"


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="perfrepair.repair")
    sub = ap.add_subparsers(dest="command", required=True)
    for name in ("candidates", "test-set", "choose"):
        p = sub.add_parser(name)
        p.add_argument("--run", type=Path, required=True)
        p.add_argument("--app-name", required=True, help="output folder under <run>/repair/")
    sub.choices["candidates"].add_argument("--sites", type=Path, required=True, help="an inbound sites.json for this app")
    sub.choices["test-set"].add_argument("-o", "--out", type=Path, required=True)
    sub.choices["choose"].add_argument("--mode", default="latency")
    for name in ("edit", "harness"):
        p = sub.add_parser(name)
        p.add_argument("--run", type=Path, required=True)
        p.add_argument("--app", required=True, help="folder under <run>/apps/")
    sub.choices["edit"].add_argument("--source", type=Path, required=True, help="the app's root; only read")
    r = sub.add_parser("replay")
    r.add_argument("--benchmark", type=Path, required=True)
    r.add_argument("--energy", type=Path)
    r.add_argument("--before", required=True, help="Type|name|provider")
    r.add_argument("--after", required=True, help="Type|name|provider")
    r.add_argument("--input", type=int)
    a = ap.parse_args(argv)

    if a.command == "replay":
        energy = read_json(a.energy) if a.energy else None
        bench = read_json(a.benchmark)
        print(yaml.safe_dump(compare(side(bench, energy, *parse_qualified(a.before), a.input),
                                     side(bench, energy, *parse_qualified(a.after), a.input)), sort_keys=False))
        return 0
    if a.command in ("edit", "harness"):
        return _edit(a) if a.command == "edit" else _harness(a)
    out = a.run / DIRECTORY / a.app_name
    groups = read_json(GroupingPaths(a.run).groups)
    if a.command == "candidates":
        sites = read_json(a.sites)
        found = candidates(sites, groups)
        write_json(out / "candidates.json", {"schemaVersion": 1, "app": sites["app"], "candidates": [c.to_json() for c in found]})
        print(f"{out / 'candidates.json'}: {len(found)} call sites")
        return 0
    found = [Candidate.from_json(c) for c in read_json(out / "candidates.json")["candidates"]]
    if a.command == "test-set":
        a.out.write_text(yaml.safe_dump(build_test_set(found, groups, a.app_name), sort_keys=False))
        print(a.out)
        return 0
    choices = choose(found, read_json(rd.worthiness(a.run, a.mode) / VERDICTS))
    write_json(out / "choices.json", {"schemaVersion": 1, "mode": a.mode, "choices": choices})
    print(f"{out / 'choices.json'}: {sum(c['replacement'] is not None for c in choices)} of {len(choices)} sites replaced")
    return 0


def _load(paths: AppPaths) -> tuple[dict[str, Scope], dict[str, Replacement]]:
    scopes = {s["id"]: Scope.from_json(s) for s in read_json(paths.scopes)["scopes"]}
    replacements = {r["scope"]: Replacement.from_json(r) for r in read_json(paths.replacements)["replacements"]}
    return scopes, replacements


def _report(path: Path, problems: list[str]) -> int:
    print("\n".join(problems), file=sys.stderr)
    print(f"{path}: not written, {len(problems)} problem(s)", file=sys.stderr)
    return 1


def _edit(a: argparse.Namespace) -> int:
    paths = AppPaths(a.run, a.app)
    scopes, replacements = _load(paths)
    doc = edit_app(scopes, list(replacements.values()), a.source, paths, load_specs())
    problems = validate_edits(doc, a.app, set(scopes))
    if problems:
        return _report(paths.edits, problems)
    write_json(paths.edits, doc)
    applied = sum(e["status"] == "applied" for e in doc["edits"])
    print(f"{paths.edits}: {applied} of {len(doc['edits'])} replacements applied")
    return 0


def _harness(a: argparse.Namespace) -> int:
    paths = AppPaths(a.run, a.app)
    scopes, replacements = _load(paths)
    edits = read_json(paths.edits)
    doc = harness(paths, scopes, replacements, edits)
    problems = validate_harness(doc, a.app, paths.root, edits)
    if problems:
        return _report(paths.harness, problems)
    write_text(paths.harness, yaml.safe_dump(doc, sort_keys=False))
    print(f"{paths.harness}: {len(doc['scopes'])} scopes")
    return 0

if __name__ == "__main__":
    sys.exit(main())
