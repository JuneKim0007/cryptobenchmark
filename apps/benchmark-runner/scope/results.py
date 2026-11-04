"""After ScopedInterop: the device's verdicts into scoped-plan.yaml, and the measured cases as a prepared.yaml for conversion."""
import copy

import yaml

MEASURABLE = ("passed", "unchecked")
DEFAULT_METRICS = ("TIME",)   # RunSettings.metrics


class ScopeResultError(Exception):
    pass


def merge(plan_path, interop_path, call_site_path=None):
    """The plan, the scopes whose function is measured, and the scopes whose call site is."""
    plan = yaml.safe_load(plan_path.read_text())
    verdicts = yaml.safe_load(interop_path.read_text()) or {}
    sites = (yaml.safe_load(call_site_path.read_text()) or {}) if call_site_path else {}
    measured, call_sites = [], []
    for record in plan["scopes"]:
        if merge_call_site(record.get("callSite") or {}, sites):
            call_sites.append(record)
        if record["status"] != "compiled":
            continue
        verdict = verdicts.get(record["id"])
        if verdict is None:
            raise ScopeResultError(f"missing_verdict: scope {record['id']} compiled but has no line in {interop_path}")
        record["interop"]["result"] = verdict["interop"]
        if verdict.get("reason"):
            record["interop"]["reason"] = verdict["reason"]
        record["status"] = "measured" if verdict["interop"] in MEASURABLE else verdict["interop"]
        if record["status"] == "measured":
            measured.append(record)
    plan_path.write_text(yaml.safe_dump(plan, sort_keys=False))
    return plan, measured, call_sites


def merge_call_site(site, verdicts):
    """Both sides prepared on the device: the block records each side's prepared case; else the first side's reason."""
    if site.get("status") != "planned":
        return False
    found = [verdicts.get(case) or {"status": "not_prepared", "reason": "no_verdict: the device wrote no line"} for case in site["cases"]]
    failed = next((v for v in found if v["status"] != "prepared"), None)
    if failed:
        site.update(status="not_prepared", reason=failed["reason"])
        return False
    site.update(status="prepared", prepared=[{"folder": v["folder"], "case": v["case"]} for v in found])
    return True


def device_case(scoped, chosen):
    cases = yaml.safe_load((scoped / chosen["folder"] / "prepared.yaml").read_text())["cases"]
    found = next((c for c in cases if c["id"] == chosen["case"]), None)
    if found is None:
        raise ScopeResultError(f"missing_case: {chosen['case']} is not in {chosen['folder']}/prepared.yaml")
    return copy.deepcopy(found)


def prepared(plan, measured, effective, out, call_sites=()):
    run = (yaml.safe_load(effective.read_text()) or {}).get("run") or {}
    harness, metrics = run.get("harness") or {}, run.get("metrics") or DEFAULT_METRICS
    cases = []
    for record in measured:
        for case in record["cases"]:
            entry = {"id": case, "type": "Scope", "algorithm": record["function"], "provider": plan["app"],
                     "operation": case.rsplit(":", 1)[1], "key": {"kind": "none"}, "harness": harness,
                     "metrics": list(metrics), "resolvedParameters": {}}
            entry.update({k: record["inputs"][k] for k in ("inputSize", "keySize") if record["inputs"].get(k) is not None})
            cases.append(entry)
    for record in call_sites:
        site = record["callSite"]
        for case, chosen in zip(site["cases"], site["prepared"]):
            cases.append({**device_case(out.parent, chosen), "id": case, "harness": harness, "metrics": list(metrics)})
    document = {"schemaVersion": 1, "run": {"seed": plan["seed"], "harness": harness}, "cases": cases}
    out.write_text(yaml.safe_dump(document, sort_keys=False))
    return out


def cases_of(measured, call_sites):
    """Before and after adjacent per scope, so the session's A/B then B/A order alternates each pair."""
    return tuple(case for record in measured for case in record["cases"]) + tuple(c for r in call_sites for c in r["callSite"]["cases"])
