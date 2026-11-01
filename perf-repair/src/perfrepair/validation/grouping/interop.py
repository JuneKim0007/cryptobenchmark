from __future__ import annotations

from pathlib import Path

from ...dto.interop import RESULTS, SCHEMA_VERSION, PairResult, PlannedPair, interop_section
from ...files import read_yaml


def _members(groups: dict) -> dict[str, set[str]]:
    return {g["id"]: {groups["items"][str(m)]["qualified"] for m in g["members"]} for g in groups["groups"]}


def validate_plan(plan: dict, groups: dict) -> list[str]:
    if plan.get("schemaVersion") != SCHEMA_VERSION:
        return [f"interop_plan.yaml schemaVersion {plan.get('schemaVersion')} is not {SCHEMA_VERSION}"]
    members, problems, seen = _members(groups), [], set()
    for p in map(PlannedPair.from_json, plan["pairs"]):
        if p.id in seen:
            problems.append(f"pair {p.id}: id repeats")
        seen.add(p.id)
        if p.a == p.b:
            problems.append(f"pair {p.id}: pairs {p.a} with itself")
        if not {p.a, p.b} <= members.get(p.group, set()):
            problems.append(f"pair {p.id}: {p.a} and {p.b} are not both members of group {p.group!r}")
    return problems


def _expected(directions: dict) -> str:
    labels = {directions.get("aToB"), directions.get("bToA")}
    return "fail" if "fail" in labels else "pass" if labels == {"pass"} else "not_checkable"


def validate_results(results: dict, plan: dict) -> list[str]:
    if results.get("schemaVersion") != SCHEMA_VERSION:
        return [f"interop.yaml schemaVersion {results.get('schemaVersion')} is not {SCHEMA_VERSION}"]
    planned = {p.id: p for p in map(PlannedPair.from_json, plan["pairs"])}
    rows = results.get("pairs") or []
    problems = []
    if sorted(int(r["id"]) for r in rows) != sorted(planned):
        problems.append(f"pair ids {sorted(int(r['id']) for r in rows)} are not the plan's {sorted(planned)}")
    for row in rows:
        r, p = PairResult.from_interop(row), planned.get(int(row["id"]))
        if p is not None and (r.group, r.a, r.b) != (p.group, p.a, p.b):
            problems.append(f"pair {r.id}: {r.group} {r.a} / {r.b} is not the planned {p.group} {p.a} / {p.b}")
        if r.result not in RESULTS:
            problems.append(f"pair {r.id}: result {r.result!r} is not one of {RESULTS}")
        elif r.result != _expected(row.get("directions") or {}):
            problems.append(f"pair {r.id}: result {r.result} disagrees with directions {row.get('directions')}")
        if r.result != "pass" and not r.reason:
            problems.append(f"pair {r.id}: {r.result} without a reason")
    return problems


def validate_section(groups: dict, imported: list[PairResult] | None) -> list[str]:
    section = groups.get("interop")
    if section is None:
        return ["groups.json has no interop section; rerun grouping report"]
    if section != interop_section(imported):
        return ["groups.json interop section differs from grouping/interop.yaml; rerun grouping report"]
    return []


def validate_interop(run: Path, groups: dict, plan_path: Path, results_path: Path) -> dict[str, list[str]]:
    out: dict[str, list[str]] = {}
    imported = None
    if plan_path.exists():
        plan = read_yaml(plan_path)
        out["grouping/interop_plan.yaml"] = validate_plan(plan, groups)
        if results_path.exists():
            results = read_yaml(results_path)
            out["grouping/interop.yaml"] = validate_results(results, plan)
            imported = [PairResult.from_interop(r) for r in results.get("pairs") or []]
    elif results_path.exists():
        out["grouping/interop.yaml"] = ["interop.yaml without the interop_plan.yaml it answers"]
    out["grouping/groups.json interop"] = validate_section(groups, imported)
    return out
