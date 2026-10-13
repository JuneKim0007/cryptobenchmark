"""python3 -m perfrepair.repair — call sites → test set → replacements → patches → before/after."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import yaml

from .. import run_dir as rd
from ..dto.grouping import parse_qualified
from ..files import read_json, write_json
from ..grouping.paths import GroupingPaths
from ..orchestrate.decisions.worthiness import VERDICTS
from ..validation.repair import validate_patch
from .candidates import Candidate, candidates
from .choose import choose
from .patch import rewrite
from .replay import compare, side
from .test_set import build_test_set

DIRECTORY = "repair"


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="perfrepair.repair")
    sub = ap.add_subparsers(dest="command", required=True)
    for name in ("candidates", "test-set", "choose", "patch"):
        p = sub.add_parser(name)
        p.add_argument("--run", type=Path, required=True)
        p.add_argument("--app-name", required=True, help="output folder under <run>/repair/")
    sub.choices["candidates"].add_argument("--sites", type=Path, required=True, help="an inbound sites.json for this app")
    sub.choices["test-set"].add_argument("-o", "--out", type=Path, required=True)
    sub.choices["choose"].add_argument("--mode", default="latency")
    sub.choices["patch"].add_argument("--app", type=Path, required=True)
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
    if a.command == "choose":
        choices = choose(found, read_json(rd.worthiness(a.run, a.mode) / VERDICTS))
        write_json(out / "choices.json", {"schemaVersion": 1, "mode": a.mode, "choices": choices})
        print(f"{out / 'choices.json'}: {sum(c['replacement'] is not None for c in choices)} of {len(choices)} sites replaced")
        return 0
    patches, problems = [], []
    for choice in read_json(out / "choices.json")["choices"]:
        if choice["replacement"] is None:
            continue
        site = Candidate.from_json(choice["site"])
        _, _, resolved = parse_qualified(groups["items"][site.item]["qualified"])
        _, name, provider = parse_qualified(groups["items"][choice["replacement"]]["qualified"])
        patch = rewrite(site, resolved, name, provider, a.app).to_json()
        problems += validate_patch(patch, a.app)
        patches.append(patch)
    if problems:
        print("\n".join(problems), file=sys.stderr)
        return 1
    write_json(out / "patches.json", {"schemaVersion": 1, "patches": patches})
    print(f"{out / 'patches.json'}: {len(patches)} patches")
    return 0


if __name__ == "__main__":
    sys.exit(main())
