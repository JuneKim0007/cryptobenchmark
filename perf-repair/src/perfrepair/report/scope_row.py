"""One scope's report row: each step's status and reason, joined by scope id; the first step that stops names
why the metrics are not measured."""
from __future__ import annotations

from ..dto import MetricComparison, PairMetrics
from ..dto.report import CALL_SITE, FUNCTION, MEASURABLE, call_site_case_id, case_id
from ..dto.units import DisplayUnits
from ..result.gain import label_of
from ..result.modes import Mode
from ..result.category import at_call_site, checkable, truth
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


def _call_site_metrics(site: dict | None, before: dict | None, after: dict | None, mode: Mode, units: DisplayUnits) -> list[dict]:
    if not site or site.get("status") != "prepared":
        reason = f"{site.get('status')}: {site.get('reason')}" if site else "no_call_site: the plan has no callSite"
        return unmeasured(f"call site {reason}", mode.perf)
    if before is None or after is None:
        return unmeasured("no_cases: the device measured neither or one of the call's before and after", mode.perf)
    return metric_rows(before, after, mode.perf, units)


def _kind(name: str, scope: dict, metrics: list[dict], before: dict | None, after: dict | None, mode: Mode, current: str | None,
          option: str | None, estimates: list[dict]) -> dict:
    return {"metrics": metrics, "label": _label(metrics), "verdict": _verdict(mode, current, option, metrics) if option else "not_measured",
            "thermal": thermal_row(before, after), "truth": truth(name, scope["pattern"], metrics, estimates)}


def _truth_check(by: str | None, scope: dict) -> str:
    if by == CALL_SITE:
        return "per_call: the swapped call alone"
    return "per_call" if checkable(scope) else "not_applicable: the before/after times the setup function of a fixed scope"


def _measured_by(kinds: dict) -> str | None:
    """The function when it has a number, else the call alone."""
    return next((name for name in (FUNCTION, CALL_SITE) if any(m["measured"] for m in kinds[name]["metrics"])), None)


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
    site = (record or {}).get("callSite")
    site_before, site_after = (measured.cases.get(call_site_case_id(scope["id"], side)) for side in ("before", "after"))
    site_metrics = metrics if decision["decision"] != "replace" or edited["status"] != "applied" else _call_site_metrics(site, site_before, site_after, mode, units)
    kinds = {FUNCTION: _kind(FUNCTION, scope, metrics, before, after, mode, current, option, primitive),
             CALL_SITE: {**_kind(CALL_SITE, scope, site_metrics, site_before, site_after, mode, current, option,
                                 at_call_site(primitive, (site or {}).get("operation"), inputs)), "operation": (site or {}).get("operation")}}
    by = _measured_by(kinds)
    chosen = kinds[by or FUNCTION]
    return {"scope": scope["id"], "file": scope["file"], "line": scope["line"], "function": scope["function"],
            "pattern": scope["pattern"], "patternReason": scope["patternReason"], "current": current, "option": option, "inputs": inputs, "decision": decision, "edit": edited, "compile": compiled,
            "interop": interop, "metrics": chosen["metrics"],
            "verdict": chosen["verdict"],
            "label": chosen["label"], "thermal": chosen["thermal"],
            "deciding": list((replacement or {}).get("deciding") or ()), "accepted": list((replacement or {}).get("accepted") or ()),
            "primitive": primitive, "categoryMismatch": chosen["truth"]["mismatch"],
            "truthCheck": _truth_check(by, scope), "measuredBy": by, "measurements": kinds}
