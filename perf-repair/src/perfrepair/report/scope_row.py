"""One scope's report row: each step's status and reason, joined by scope id; the first step that stops names
why the metrics are not measured."""
from __future__ import annotations

from ..dto import MetricComparison, PairMetrics
from ..dto.report import MEASURABLE, case_id
from ..dto.units import DisplayUnits
from ..result.gain import label_of
from ..result.modes import Mode
from ..result.category import category_mismatch
from .measured import Measured
from .metrics import metric_rows, unmeasured
from .thermal import thermal_row


def _step(status: str, reason: str | None = None, **extra) -> dict:
    return {"status": status, "reason": reason, **extra}


def _compile(record: dict | None, measured: Measured, applied: bool) -> dict:
    if not applied:
        return _step("skipped", "no applied edit")
    if measured.absent:
        return _step("not_run", measured.absent)
    if record["status"] == "not_measurable":
        return _step("not_measurable", record.get("reason"))
    if record["status"] == "not_compilable":
        detail = record.get("identifiers") or record.get("compilerErrors")
        reason = record.get("reason") + (f": {', '.join(detail)}" if detail else "")
        return _step("primitive_only", reason)
    return _step("compiled")


def _interop(record: dict | None, compiled: dict) -> dict:
    if compiled["status"] != "compiled":
        return _step("skipped" if compiled["status"] != "not_run" else "not_run", compiled["reason"], check=None)
    check = (record.get("interop") or {}).get("check")
    result = (record.get("interop") or {}).get("result")
    if result is None:
        return _step("not_run", "no_verdict: the device run ended before the interop check", check=check)
    status = result if result in MEASURABLE else record["status"]
    return _step(status, (record.get("interop") or {}).get("reason"), check=check)


def _verdict(mode: Mode, current: str, option: str, metrics: list[dict]) -> str:
    measured = tuple(MetricComparison(m["metric"], m["ratio"], m["pImprove"], m["level"], m["n"]) for m in metrics if m["measured"])
    return mode.judge(PairMetrics(current, option, "n/a", measured))


def _label(metrics: list[dict]) -> str:
    """Over the selected metrics measured: the change of each, per the one rule of result/gain.py."""
    return label_of([m["change"] for m in metrics if m["measured"] and m["selected"]])


def _decision(replacement: dict | None, source: str | None, stale: bool) -> dict:
    if replacement is None:
        return {"decision": "not_run", "reason": "no replacements.json row (not asked yet)", "source": None, "stale": False,
                "needs": [], "concerns": []}
    return {"decision": replacement["decision"], "reason": replacement["reason"], "source": source, "stale": stale,
            "needs": list(replacement.get("needs") or ()), "concerns": list(replacement.get("concerns") or ())}


def _edit(edit: dict | None, decision: dict, has_edits: bool) -> dict:
    if decision["decision"] != "replace":
        return _step("skipped", f"decision {decision['decision']}")
    if not has_edits:
        return _step("not_run", "no edits.json")
    blocked = f": {edit['blockedBy']}" if edit.get("blockedBy") else ""
    return _step(edit["status"], (edit["reason"] + blocked) if edit["reason"] else None)


def scope_row(scope: dict, dossier: dict | None, replacement: dict | None, source: str | None, edit: dict | None,
              has_edits: bool, measured: Measured, mode: Mode, inputs: dict | None, units: DisplayUnits,
              stale: bool = False) -> dict:
    """`inputs`: the scope's harness.yaml inputs with their source; None when the scope is not in the harness.
    `stale`: the decision was made on an earlier dossier."""
    decision = _decision(replacement, source, stale)
    edited = _edit(edit, decision, has_edits)
    record = measured.plan.get(scope["id"])
    compiled = _compile(record, measured, edited["status"] == "applied")
    interop = _interop(record, compiled)
    option = replacement["option"] if replacement else None
    current = dossier["current"] if dossier else None
    before, after = (measured.cases.get(case_id(scope["id"], side)) for side in ("before", "after"))
    stop = next((s for s in (edited, compiled, interop) if s["status"] not in ("applied", "compiled", *MEASURABLE)),
                None)
    if decision["decision"] != "replace":
        metrics = unmeasured(f"not replaced: {decision['decision']} ({decision['reason']})", mode.perf)
    elif stop is not None:
        metrics = unmeasured(f"{stop['status']}: {stop['reason']}", mode.perf)
    elif before is None or after is None:
        metrics = unmeasured("no_cases: the device measured neither or one of before and after", mode.perf)
    else:
        metrics = metric_rows(before, after, mode.perf, units)
    primitive = next((o["estimates"] for o in (dossier or {}).get("options") or [] if o["item"] == option), [])
    return {"scope": scope["id"], "file": scope["file"], "line": scope["line"], "function": scope["function"],
            "pattern": scope["pattern"], "patternReason": scope["patternReason"], "current": current, "option": option, "inputs": inputs, "decision": decision, "edit": edited, "compile": compiled,
            "interop": interop, "metrics": metrics,
            "verdict": _verdict(mode, current, option, metrics) if option else "not_measured",
            "label": _label(metrics), "thermal": thermal_row(before, after),
            "deciding": list((replacement or {}).get("deciding") or ()), "accepted": list((replacement or {}).get("accepted") or ()),
            "primitive": primitive, "categoryMismatch": category_mismatch(metrics, primitive)}
