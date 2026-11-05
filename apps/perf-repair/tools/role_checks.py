"""On demand, a real model, never in CI: per role, app and run, on copies of a device folder: flips, a removed input, a rerun
and known answers, one report with cost; the command is in docs/decisions.md, the plan in tools/role-checks.example.yaml."""
from __future__ import annotations

import argparse
import json
import shutil
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

import yaml

from perfrepair import run_dir as rd
from perfrepair.ai.evaluate.worthiness import command as worthiness
from perfrepair.ai.parse.algorithm_classify import command as classify
from perfrepair.ai.parse.grouping_assign import command as assign
from perfrepair.ai.repair.upgrade import command as upgrade
from perfrepair.ai.review.grouping_review import command as review
from perfrepair.ai.runtime.engine.events import TOKEN_KEYS
from perfrepair.ai.runtime.engine.outbox import active_outbox
from perfrepair.ai.runtime.engine.tracking import MissingInput
from perfrepair.ai.runtime.gateway.args import add_agent_args
from perfrepair.ai.runtime.gateway.spawn import spawn
from perfrepair.ai.runtime.prompt.args import add_prompt_args, load_prompts
from perfrepair.ai.suggest.site_replace import command as replace
from perfrepair.catalog.role_contracts import RoleContract, role_contracts
from perfrepair.config.args import load_settings
from perfrepair.dto.classify import read_batches
from perfrepair.dto.perf_mode import PerfMode
from perfrepair.files import read_json, sha256_text, write_json
from perfrepair.inputs import table
from perfrepair.result.modes import mode_of
from perfrepair.review import stability

FREE_TEXT = ("reason", "description", "concerns")
QUIET = {"echo": lambda _: None}


@dataclass(frozen=True)
class Context:
    library: object
    app: str
    mode: str


def _classify(device: Path, conversations, c: Context) -> None:
    paths = rd.GroupingPaths(device)
    reviewer = classify.Reviewer(conversations, c.library)
    classify.classify(paths, read_batches(read_json(paths.classify_batches)), rd.load_screen(paths), reviewer, **QUIET)


@dataclass(frozen=True)
class Runner:
    row: table.RoleRow
    dry_run: object
    run: Callable


RUNNERS = {
    "screening.classify": Runner(table.SCREENING_CLASSIFY, classify.DRY_RUN, _classify),
    "grouping.assign": Runner(table.GROUPING_ASSIGN, assign.DRY_RUN,
                              lambda d, a, c: assign.assign(rd.GroupingPaths(d), a, c.library)),
    "grouping.supervisor": Runner(table.GROUPING_SUPERVISOR, review.DRY_RUN,
                                  lambda d, a, c: review.review(rd.GroupingPaths(d), a, c.library, **QUIET)),
    "worthiness": Runner(table.WORTHINESS, worthiness.DRY_RUN,
                         lambda d, a, c: worthiness.worthiness(d, mode_of(PerfMode.parse(c.mode)), a, c.library, **QUIET)),
    "apps.replace": Runner(table.APPS_REPLACE, replace.DRY_RUN, lambda d, a, c: replace.replace(d, c.app, a, c.library, **QUIET)),
    "repair-upgrade": Runner(table.APPS_UPGRADE, upgrade.DRY_RUN, lambda d, a, c: upgrade.upgrade(d, c.app, a, c.library, **QUIET)),
    "review.stability": Runner(table.APPS_REPLACE, replace.DRY_RUN,
                               lambda d, a, c: stability.stability(d, a, c.library, sample=3, asks=3)),
}


def _names(role: str, c: Context) -> dict:
    return {k: v for k, v in (("app", c.app), ("mode", c.mode)) if "{" + k + "}" in role_contracts()[role].folder}


def contract_of(role: str, c: Context) -> RoleContract:
    return role_contracts()[role].bind(**_names(role, c))


def _fresh(source: Path, target: Path, row: RoleContract) -> Path:
    """A copy with the role's own results gone, so it asks again."""
    shutil.rmtree(target, ignore_errors=True)
    shutil.copytree(source, target)
    folder = target / row.folder
    shutil.rmtree(folder / "outbox", ignore_errors=True)
    for name in (rd.JOURNAL, "errors.jsonl", rd.ROLE_WRITES):
        (folder / name).unlink(missing_ok=True)
    return target


def _picks(device: Path, row: RoleContract) -> dict:
    """Each item's decision with the free text left out."""
    def plain(x):
        if isinstance(x, dict):
            return {k: plain(v) for k, v in x.items() if k not in FREE_TEXT}
        return [plain(v) for v in x] if isinstance(x, list) else x
    return {r.item: plain(r.decision) for r in active_outbox(device / row.folder).records()}


def _usage(device: Path, row: RoleContract) -> dict:
    path = device / row.folder / rd.JOURNAL
    lines = [json.loads(line) for line in path.read_text().splitlines()] if path.is_file() else []
    usages = [(t.get("reply") or {}).get("usage") or {} for t in lines]
    return {"calls": len(lines), "promptTokens": [t["promptTokens"] for t in lines],
            **{k: sum(int(u.get(k) or 0) for u in usages) for k in TOKEN_KEYS},
            "costUsd": round(sum(u.get("costUsd") or 0 for u in usages), 6)}


def _flipped(device: Path, flip: dict, c: Context) -> None:
    path = device / flip["file"].format(app=c.app, mode=c.mode)
    if "swap" in flip:
        doc = read_json(path)
        at = doc[flip["under"]]
        a, b = flip["swap"]
        at[a], at[b] = at[b], at[a]
        write_json(path, doc)
        return
    text = path.read_text()
    if flip["old"] not in text:
        raise ValueError(f"flip {flip['name']}: {flip['old']!r} is not in {path}")
    path.write_text(text.replace(flip["old"], flip["new"]))
    _rehash_built(device, path)


def _rehash_built(device: Path, path: Path) -> None:
    """screen.json digests the items and profiles it was built from; a flip there would be refused as another build."""
    paths = rd.GroupingPaths(device)
    key = {paths.items: "items", paths.profiles: "profiles"}.get(path)
    if key and paths.screen.is_file():
        doc = read_json(paths.screen)
        doc["built"][key] = sha256_text(path.read_text())
        write_json(paths.screen, doc)


def _matches(known: dict, picks: dict) -> dict:
    """Each known item whose decision holds the known fields."""
    asked = [k for k in known if k in picks]
    hits = sum(all((picks[k] or {}).get(f) == v for f, v in known[k].items()) for k in asked)
    return {"known": len(known), "asked": len(asked), "matched": hits, "rate": hits / len(asked) if asked else None}


def _refused(source: Path, target: Path, row: RoleContract, run, conversations, c: Context) -> bool:
    device = _fresh(source, target, row)
    for path in device.glob(next(p for p in row.required if not p.startswith("catalog/"))):
        path.unlink()
    asked = conversations()
    try:
        run(device, asked, c)
    except MissingInput:
        return getattr(asked, "started", 0) == 0
    return False


def check_role(role: str, source: Path, work: Path, conversations, c: Context, plan: dict) -> dict:
    """One role at one app and run: the baseline, then each check on its own copy."""
    row, run = contract_of(role, c), RUNNERS[role].run
    base = _fresh(source, work / "base", row)
    run(base, conversations(), c)
    picks, usage = _picks(base, row), _usage(base, row)
    run(base, conversations(), c)
    checks = {"identical rerun makes no call": _usage(base, row)["calls"] == usage["calls"]}
    for flip in (plan.get("flips") or {}).get(role, []):
        device = _fresh(source, work / f"flip-{flip['name']}", row)
        _flipped(device, flip, c)
        run(device, conversations(), c)
        checks[f"flip {flip['name']} changes the answer"] = _picks(device, row) != picks
        usage = {k: v + _usage(device, row)[k] for k, v in usage.items()}
    checks["required input removed refuses before any call"] = _refused(source, work / "removed", row, run, conversations, c)
    return {"role": role, "app": c.app, "checks": checks, "pass": all(checks.values()), "usage": usage,
            "knownAnswers": _matches((plan.get("known") or {}).get(role, {}), picks)}


def check_all(source: Path, out: Path, apps: list[str], runs: int, mode: str, plan: dict, conversations_of, library) -> dict:
    rows = []
    for app in apps:
        c = Context(library, app, mode)
        for n in range(1, runs + 1):
            for role in RUNNERS:
                if role == "screening.classify" and not rd.GroupingPaths(source).classify_batches.is_file():
                    continue
                found = check_role(role, source, out / app / f"run-{n}" / role, lambda r=role: conversations_of(r), c, plan)
                rows.append({**found, "run": n})
    return {"rows": rows, "pass": all(r["pass"] for r in rows), "costUsd": round(sum(r["usage"]["costUsd"] for r in rows), 6)}


def _print(report: dict) -> None:
    print("role | app | run | result | calls | input | output | cost")
    for r in report["rows"]:
        u = r["usage"]
        print(f"{r['role']} | {r['app']} | {r['run']} | {'pass' if r['pass'] else 'FAIL'} | {u['calls']} | {u['input']} | "
              f"{u['output']} | {u['costUsd']}")
        for name, ok in r["checks"].items():
            if not ok:
                print(f"  failed: {name}")
    print(f"total cost: {report['costUsd']} USD")


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--device-results", type=Path, required=True)
    ap.add_argument("--apps", required=True, help="comma-separated app folders")
    ap.add_argument("--runs", type=int, default=3)
    ap.add_argument("--mode", required=True, help="a worthiness folder's perfMode name")
    ap.add_argument("--plan", type=Path, required=True)
    ap.add_argument("--out", type=Path, required=True)
    add_agent_args(ap, table.APPS_REPLACE)
    add_prompt_args(ap)
    a = ap.parse_args(argv)
    settings = load_settings(ap, a)

    def conversations_of(role: str):
        a.agent_role = RUNNERS[role].row
        return spawn(a, settings, RUNNERS[role].dry_run)
    report = check_all(a.device_results, a.out, a.apps.split(","), a.runs, a.mode, yaml.safe_load(a.plan.read_text()),
                       conversations_of, load_prompts(ap, a, settings))
    write_json(a.out / "report.json", report)
    _print(report)
    return 0 if report["pass"] else 1


if __name__ == "__main__":
    sys.exit(main())
