"""results/<device_id>/manifest.yaml: what a finished run wrote, measured and survived."""
import json

import energy_stage
from device import clocks
from device.identity import device_id
from results import layout as results_layout
from results import run_inputs


def runtime(measured, probe, files):
    document = dict(measured["runtime"] if measured else probe.get("runtime") or {})
    if "clocks" in files:
        paths = files["clocks"] if isinstance(files["clocks"], list) else [files["clocks"]]
        document["cpuLocked"] = clocks.runtime_locked(paths)
    return document


def units(files):
    """analysis.units as :config wrote it into effective.yaml: the display units every view of this run reads."""
    import yaml
    effective = yaml.safe_load(files["effective"].read_text()) if "effective" in files else None
    found = ((effective or {}).get("analysis") or {}).get("units")
    return {"units": found} if found else {}


def survived(problems):
    return {"problems": list(problems)} if problems else {}


def manifest(results, mode, configuration, files, problems=()):
    import yaml
    def load(key):
        text = files[key].read_text()
        return json.loads(text) if files[key].suffix == ".json" else yaml.safe_load(text)
    probe = load("probe") if "probe" in files else {}
    measured = load("benchmark") if "benchmark" in files else None
    counted = {"prepared": ("prepared", "cases"), "skipped": ("skipped", "skipped"), "measured": ("benchmark", "cases")}
    document = {
        "schemaVersion": 1,
        "mode": mode,
        "config": str(configuration),
        "deviceId": device_id(probe.get("runtime") or {}),
        "inputs": run_inputs.digests(configuration),
        "runtime": runtime(measured, probe, files),
        "providers": [{"name": p["name"], "precedence": p["precedence"], "serviceCount": len(p.get("services") or [])}
                      for p in sorted(probe.get("providers") or [], key=lambda p: p["precedence"])],
        "files": {key: [path.relative_to(results).as_posix() for path in value] if isinstance(value, list)
                  else value.relative_to(results).as_posix() for key, value in files.items()},
        "counts": {count: len((measured if key == "benchmark" else load(key)).get(field) or [])
                   for count, (key, field) in counted.items() if key in files},
    } | units(files) | energy_stage.estimated_mark(files.get("energy")) | survived(problems)
    path = results / results_layout.MANIFEST
    results_layout.write_atomic(path, yaml.safe_dump(document, sort_keys=False))
    print(f"wrote:     {path}")


def add_to_manifest(results, added):
    import yaml
    path = results / results_layout.MANIFEST
    document = yaml.safe_load(path.read_text())
    document["files"].update({key: value.relative_to(results).as_posix() for key, value in added.items()})
    results_layout.write_atomic(path, yaml.safe_dump(document, sort_keys=False))
    print(f"wrote:     {path}")
