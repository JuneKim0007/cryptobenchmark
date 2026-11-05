"""After ScopedInterop: the device's verdicts into scoped-plan.yaml."""
import yaml

MEASURABLE = ("passed", "unchecked")


class ScopeResultError(Exception):
    pass


def merge(plan_path, interop_path):
    plan = yaml.safe_load(plan_path.read_text())
    verdicts = yaml.safe_load(interop_path.read_text()) or {}
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
    plan_path.write_text(yaml.safe_dump(plan, sort_keys=False))
    return plan
