"""results/<device_id>/manifest.yaml: what a finished run wrote, measured and survived."""
import json

from device import clocks
from device.capture import runtime as capture_runtime
from device.identity import device_id
from results import layout as results_layout
from cryptobench import paths
from results import run_inputs
from cryptobench.document import parse_yaml, read_yaml

ENGINE_OPERATIONS = paths.repo().engine_operations


def runtime(measured, captured, files):
    document = dict(measured["runtime"] if measured else captured)
    if "clocks" in files:
        paths = files["clocks"] if isinstance(files["clocks"], list) else [files["clocks"]]
        document["cpuLocked"] = clocks.runtime_locked(paths)
    return document


def units(files):
    """analysis.units as :config wrote it into effective.yaml: the display units every view of this run reads."""
    import yaml
    effective = read_yaml(files["effective"]) if "effective" in files else None
    found = ((effective or {}).get("analysis") or {}).get("units")
    return {"units": found} if found else {}


def estimated_mark(energy_files):
    """The manifest's mark of a run whose energy is estimated; a measured run has none."""
    paths = energy_files if isinstance(energy_files, list) else [energy_files] if energy_files else []
    documents = [json.loads(path.read_text()) for path in paths]
    sources = sorted({d["source"] for d in documents if d.get("kind") == "estimated"})
    return {"energy": {"source": ", ".join(sources), "kind": "estimated"}} if sources else {}


def operations():
    """Per engine type the operations the harness times, so a reader of the run needs no path into this repository."""
    import yaml
    return {t: list(ops) for t, ops in (read_yaml(ENGINE_OPERATIONS).get("types") or {}).items()}


def survived(problems):
    return {"problems": list(problems)} if problems else {}


def manifest(results, mode, configuration, files, problems=()):
    import yaml
    def load(key):
        text = files[key].read_text()
        return json.loads(text) if files[key].suffix == ".json" else parse_yaml(text, str(files[key]))
    probe = load("probe") if "probe" in files else {}
    measured = load("benchmark") if "benchmark" in files else None
    captured = capture_runtime(probe)
    counted = {"prepared": ("prepared", "cases"), "skipped": ("skipped", "skipped"), "measured": ("benchmark", "cases")}
    document = {
        "schemaVersion": 1,
        "mode": mode,
        "config": str(configuration),
        "deviceId": device_id(captured),
        "inputs": run_inputs.digests(configuration),
        "runtime": runtime(measured, captured, files),
        "providers": [{"name": p["name"], "precedence": p["precedence"], "serviceCount": len(p.get("services") or [])}
                      for p in sorted(probe.get("providers") or [], key=lambda p: p["precedence"])],
        "files": {key: [path.relative_to(results).as_posix() for path in value] if isinstance(value, list)
                  else value.relative_to(results).as_posix() for key, value in files.items()},
        "counts": {count: len((measured if key == "benchmark" else load(key)).get(field) or [])
                   for count, (key, field) in counted.items() if key in files},
        "operations": operations(),
    } | units(files) | estimated_mark(files.get("energy")) | survived(problems)
    path = paths.RunTree(results).manifest
    results_layout.write_atomic(path, yaml.safe_dump(document, sort_keys=False))
    print(f"wrote:     {path}")


def add_to_manifest(results, added):
    import yaml
    path = paths.RunTree(results).manifest
    document = read_yaml(path)
    document["files"].update({key: value.relative_to(results).as_posix() for key, value in added.items()})
    results_layout.write_atomic(path, yaml.safe_dump(document, sort_keys=False))
    print(f"wrote:     {path}")
