"""results/<device_id>/manifest.yaml: what a finished run wrote, measured and survived."""
import json

from cryptobench.shared.device import clocks
from cryptobench.shared.device.capture import runtime as capture_runtime
from cryptobench.shared.device.identity import device_id
from cryptobench.shared import paths
from cryptobench.shared.results import run_inputs
from cryptobench.shared.settings.effective_view import AnalysisView, found
from cryptobench.shared.document.document import DocumentKind, parse_yaml, read_yaml
from cryptobench.shared.document.dump import dump_yaml
from cryptobench.shared.document.write import MANIFEST, write_text
from cryptobench.shared.log.stdout import WROTE, say

ENGINE_OPERATIONS = paths.repo().engine_operations
MANIFEST_DOC = DocumentKind("manifest", 1)
MODES = ("host", "device")


def runtime(measured, captured, files):
    document = dict(measured["runtime"] if measured else captured)
    if "clocks" in files:
        paths = files["clocks"] if isinstance(files["clocks"], list) else [files["clocks"]]
        document["cpuLocked"] = clocks.runtime_locked(paths)
    return document


def units(files):
    """analysis.units as :config wrote it into effective.yaml: the display units every view of this run reads."""
    effective = read_yaml(files["effective"]) if "effective" in files else {}
    return {"units": AnalysisView(effective).units} if found(effective, "analysis.units") else {}


def estimated_mark(energy_files):
    """The manifest's mark of a run whose energy is estimated; a measured run has none."""
    paths = energy_files if isinstance(energy_files, list) else [energy_files] if energy_files else []
    documents = [json.loads(path.read_text()) for path in paths]
    sources = sorted({d["source"] for d in documents if d.get("kind") == "estimated"})
    return {"energy": {"source": ", ".join(sources), "kind": "estimated"}} if sources else {}


def operations():
    """Per engine type the operations the harness times, so a reader of the run needs no path into this repository."""
    return {t: list(ops) for t, ops in (read_yaml(ENGINE_OPERATIONS).get("types") or {}).items()}


def survived(problems):
    """Each line once, in first order: a skip every process meets is one line here; the block records keep each process's."""
    return {"problems": list(dict.fromkeys(problems))} if problems else {}


def manifest(results, mode, configuration, files, problems=(), partial=None, resumed=(), run=None):
    """partial: the record of a run that stopped, which marks the manifest unfinished (paths.finished); resumed: per pass the blocks an earlier
    run measured and this one kept; run: the run's record (run_record.py), the identity of every block it wrote."""
    def load(key):
        text = files[key].read_text()
        return json.loads(text) if files[key].suffix == ".json" else parse_yaml(text, str(files[key]))
    probe = load("probe") if "probe" in files else {}
    measured = load("benchmark") if "benchmark" in files else None
    captured = capture_runtime(probe)
    counted = {"prepared": ("prepared", "cases"), "skipped": ("skipped", "skipped"), "measured": ("benchmark", "cases")}
    document = {
        "schemaVersion": MANIFEST_DOC.version,
        "mode": mode,
        "config": str(configuration),
        "deviceId": device_id(captured),
        "inputs": run_inputs.digests(configuration),
        **({"run": run} if run else {}),
        "runtime": runtime(measured, captured, files),
        "providers": [{"name": p["name"], "precedence": p["precedence"], "serviceCount": len(p.get("services") or [])}
                      for p in probe.get("providers") or []],
        "files": {key: [path.relative_to(results).as_posix() for path in value] if isinstance(value, list)
                  else value.relative_to(results).as_posix() for key, value in files.items()},
        "counts": {count: len((measured if key == "benchmark" else load(key)).get(field) or [])
                   for count, (key, field) in counted.items() if key in files},
        "operations": operations(),
    } | units(files) | estimated_mark(files.get("energy")) | survived(problems) | ({"resumed": list(resumed)} if resumed else {}) | ({"partial": partial} if partial else {})
    say(WROTE, write(results, document))


def write(results, document):
    """manifest.yaml replaced whole through its hidden temporary; every writer of a manifest goes through here."""
    return write_text(paths.RunTree(results).manifest, dump_yaml(document), staging=MANIFEST)


def add_to_manifest(results, added):
    document = MANIFEST_DOC.read(paths.RunTree(results).manifest)
    document["files"].update({key: value.relative_to(results).as_posix() for key, value in added.items()})
    say(WROTE, write(results, document))
