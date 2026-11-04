"""Each swap's call site alone: the current and the option item as benchmark selections at the scope's sizes, operation and variant."""
import copy

import yaml

SIDES = ("before", "after")
PLAN = "callsite.yaml"   # CallSitePlan.FILE
PREFIX = "callsite-"     # one effective per selection, its prepared.yaml in the folder of that name


def case_id(scope_id, side):
    return f"scope:{scope_id}:callSite:{side}"


def item(text):
    parts = str(text or "").split("|")
    return dict(zip(("type", "algorithm", "provider"), parts)) if len(parts) == 3 and all(parts) else None


def planned(scope):
    """The record's callSite block: planned with both sides' selections, or not_measurable with the reason."""
    site = scope.call_site
    if site is None:
        return {"status": "not_measurable", "reason": "no_call_site: harness.yaml has no callSite"}
    block = {"operation": site["operation"], "variant": site["variant"]}
    sides = {"before": item(scope.current), "after": item(scope.option)}
    if site["operation"] is None:
        return {**block, "status": "not_measurable", "reason": "no_operation: the scope performs no single benchmark operation"}
    if None in sides.values():
        return {**block, "status": "not_measurable", "reason": f"not_an_item: current {scope.current!r}, option {scope.option!r}"}
    if sides["before"]["type"] != sides["after"]["type"]:
        return {**block, "status": "not_measurable", "reason": "type_changed: current and option are different engine types"}
    sizes = {k: v for k, v in (("keySize", scope.key_size), ("inputSize", scope.input_size)) if v is not None}
    return {**block, "status": "planned", "cases": [case_id(scope.id, side) for side in SIDES],
            "sides": {side: {**sides[side], **sizes} for side in SIDES}}


def selection_key(side, operation, variant):
    return (side["type"], side["algorithm"], side["provider"], operation, side.get("keySize"), side.get("inputSize"), variant)


def entries(document, side, operation):
    """The run's configured entries of the item, narrowed to one operation and the side's sizes."""
    by_name = ((document.get("providers") or {}).get(side["provider"]) or {}).get(side["type"]) or {}
    found = {key: dict(entry or {}) for key, entry in by_name.items() if key.split("@")[0].lower() == side["algorithm"].lower()}
    found = found or {side["algorithm"]: {}}
    for entry in found.values():
        entry["operations"] = [operation]
        for field, size in (("keySizes", side.get("keySize")), ("inputSizes", side.get("inputSize"))):
            if size is not None:
                entry[field] = [size]
    return found


def effective(document, side, operation, variant):
    """The run's effective.yaml with one item: the device prepares it like any benchmark case, and the run's settings stay."""
    out = copy.deepcopy(document)
    run = out.setdefault("run", {})
    run["variants"] = [variant]
    run["phases"] = ["WARM"] if "WARM" in (run.get("phases") or ["WARM"]) else run["phases"][:1]
    out["policy"] = {**(out.get("policy") or {}), "onFailure": "skip"}
    out["providers"] = {side["provider"]: {side["type"]: entries(document, side, operation)}}
    return out


def write(records, effective_path, out):
    """callsite.yaml, empty when nothing is planned so it replaces a last run's, and one effective per distinct selection; the files to push."""
    document = yaml.safe_load(effective_path.read_text()) or {}
    selections, cases = {}, []
    for record in records:
        site = record.get("callSite") or {}
        if site.get("status") != "planned":
            continue
        for side, case in zip(SIDES, site["cases"]):
            chosen = site["sides"][side]
            key = selection_key(chosen, site["operation"], site["variant"])
            name = selections.setdefault(key, (f"{PREFIX}{len(selections) + 1}", chosen, site["operation"], site["variant"]))[0]
            cases.append({"id": case, "effective": f"{name}.yaml", "folder": name, "operation": site["operation"],
                          "variant": site["variant"], **chosen})
    files = [out / PLAN]
    files[0].write_text(yaml.safe_dump({"schemaVersion": 1, "cases": cases}, sort_keys=False))
    for name, chosen, operation, variant in selections.values():
        files.append(out / f"{name}.yaml")
        files[-1].write_text(yaml.safe_dump(effective(document, chosen, operation, variant), sort_keys=False))
    return files
