"""After ScopedBenchmark: the device's interop verdicts into scoped-plan.yaml, and the measured cases as a prepared.yaml for conversion."""
import yaml

MEASURABLE = ("passed", "unchecked")


class ScopeResultError(Exception):
    pass


def merge(plan_path, interop_path):
    plan = yaml.safe_load(plan_path.read_text())
    verdicts = yaml.safe_load(interop_path.read_text()) or {}
    measured = []
    for record in plan["scopes"]:
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
    return plan, measured


def prepared(plan, measured, effective, out):
    harness = ((yaml.safe_load(effective.read_text()) or {}).get("run") or {}).get("harness") or {}
    cases = []
    for record in measured:
        for case in record["cases"]:
            entry = {"id": case, "type": "Scope", "algorithm": record["function"], "provider": plan["app"],
                     "operation": case.rsplit(":", 1)[1], "key": {"kind": "none"}, "harness": harness}
            entry.update({k: v for k, v in record["inputs"].items() if v is not None})
            cases.append(entry)
    document = {"schemaVersion": 1, "run": {"seed": plan["seed"], "harness": harness}, "cases": cases}
    out.write_text(yaml.safe_dump(document, sort_keys=False))
    return out
