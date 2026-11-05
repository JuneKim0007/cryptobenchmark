"""One scope's report row: each step's status and reason, joined by scope id."""
from __future__ import annotations

from .device_check import DeviceCheck


def _step(status: str, reason: str | None = None, **extra) -> dict:
    return {"status": status, "reason": reason, **extra}


def _compile(record: dict | None, check: DeviceCheck, applied: bool) -> dict:
    if not applied:
        return _step("skipped", "no applied edit")
    if check.absent:
        return _step("not_run", check.absent)
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
    return _step(result, (record.get("interop") or {}).get("reason"), check=check)


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
              has_edits: bool, check: DeviceCheck, inputs: dict | None, stale: bool = False) -> dict:
    """`inputs`: the scope's harness.yaml inputs with their source; None when the scope is not in the harness.
    `stale`: the decision was made on an earlier dossier."""
    decision = _decision(replacement, source, stale)
    edited = _edit(edit, decision, has_edits)
    record = check.plan.get(scope["id"])
    compiled = _compile(record, check, edited["status"] == "applied")
    option = replacement["option"] if replacement else None
    primitive = next((o["estimates"] for o in (dossier or {}).get("options") or [] if o["item"] == option), [])
    return {"scope": scope["id"], "file": scope["file"], "line": scope["line"], "function": scope["function"],
            "pattern": scope["pattern"], "patternReason": scope["patternReason"], "current": dossier["current"] if dossier else None,
            "option": option, "inputs": inputs, "decision": decision, "edit": edited, "compile": compiled,
            "interop": _interop(record, compiled),
            "deciding": list((replacement or {}).get("deciding") or ()), "accepted": list((replacement or {}).get("accepted") or ()),
            "primitive": primitive}
