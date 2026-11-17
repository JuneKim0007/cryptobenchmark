"""index.yaml: one listing across a session's runs, read from the files each run wrote: per case its suite (the tier), device, target,
whether configured, prepared or skipped (with the code), how many runs measured it, and its from:; records read this, never regenerate ids."""
from __future__ import annotations

import json
from pathlib import Path

from cryptobench.pipeline.orchestrator.summary import Row
from cryptobench.shared import paths
from cryptobench.shared.document.document import read_yaml
from cryptobench.shared.document.dump import FLOW_LEAVES, dump_yaml
from cryptobench.shared.document.write import write_text
from cryptobench.shared.errors.coded import code_in

SCHEMA_VERSION = 1
TIME = "timeNs"


def runs_measured(benchmark: Path) -> dict[str, int]:
    """Case id -> the timed runs benchmark.json holds for it; the first metric when it has no time."""
    if not benchmark.is_file():
        return {}
    measured = {}
    for case in json.loads(benchmark.read_text()).get("cases", []):
        metrics = case.get("metrics") or {}
        metric = metrics.get(TIME) or next(iter(metrics.values()), {})
        measured[case["id"]] = len(metric.get("runs") or [])
    return measured


def skipped_case(reason: str) -> tuple[str | None, str | None]:
    """Preparation writes `<case id>: <code>: ...`, a case id ending in its variant; a reason without one is the plan's."""
    head, _, rest = reason.partition(": ")
    if rest and " " not in head and head.rsplit("_", 1)[-1] in paths.VARIANTS:
        return head, code_in(rest)
    return None, code_in(reason)


def entry_origin(effective: dict, provider: str, kind: str, name: str):
    entry = ((effective.get("providers") or {}).get(provider) or {}).get(kind, {}).get(name)
    return entry.get("from") if isinstance(entry, dict) else None


def run_cases(row: Row, unit: Path) -> list[dict]:
    tree = paths.RunTree(unit)
    base = {"suite": row.suite, "device": unit.parent.name, "target": row.target}
    effective = read_yaml(tree.configuration.effective) if tree.configuration.effective.is_file() else {}
    prepared = read_yaml(tree.preparation.prepared).get("cases", []) if tree.preparation.prepared.is_file() else []
    skips = read_yaml(tree.preparation.skipped).get("skipped", []) if tree.preparation.skipped.is_file() else []
    measured = runs_measured(tree.benchmark.json)
    cases = [{"id": c["id"], **base, "configured": True, "prepared": True, "skip": None, "runs": measured.get(c["id"], 0), "from": c.get("from")}
             for c in prepared]
    for skip in skips:
        case, code = skipped_case(str(skip.get("reason", "")))
        cases.append({"id": case, **base, "configured": True, "prepared": False, "skip": code, "runs": 0,
                      "from": entry_origin(effective, skip.get("provider"), skip.get("type"), skip.get("name"))})
    report = read_yaml(tree.configuration.report) if tree.configuration.report.is_file() else {}
    for skip in report.get("skipped") or []:
        entry = ".".join(str(skip.get(k, "*")) for k in ("provider", "type", "name"))
        cases.append({"id": None, "entry": entry, **base, "configured": False, "prepared": False, "skip": code_in(str(skip.get("reason", ""))),
                      "runs": 0, "from": None})
    return cases


def written(name: str, rows: list[Row], path: Path) -> Path:
    runs = [{"target": r.target, "suite": r.suite, "state": r.state, "code": r.code, "results": r.results} for r in rows]
    cases = [case for r in rows if r.results for case in run_cases(r, Path(r.results))]
    return write_text(path, dump_yaml({"schemaVersion": SCHEMA_VERSION, "session": name, "runs": runs, "cases": cases}, FLOW_LEAVES))
