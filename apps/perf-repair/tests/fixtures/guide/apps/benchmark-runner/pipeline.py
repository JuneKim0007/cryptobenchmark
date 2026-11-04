"""A fake `pipeline.py --device --harness`: every harness scope compiled, interop passed, after 20% faster; --identify names FAKE_HARNESS.
FAKE_EXIT fails every run, FAKE_FAIL_APP only the app of that name; FAKE_ENERGY_INVALID adds energy.json, one case invalid."""
import argparse, json, os, pathlib, sys

import yaml

parser = argparse.ArgumentParser()
parser.add_argument("--config")
parser.add_argument("--device", action="store_true")
parser.add_argument("--harness")
parser.add_argument("--identify", action="store_true")
options = parser.parse_args()
if options.identify:
    print("identity:  " + json.dumps({"deviceId": "fake-api36-00000000", "mode": "device" if options.device else "host",
                                      "config": options.config, "inputs": {},
                                      "harness": os.environ.get("FAKE_HARNESS", "fake-harness")}))
    sys.exit(0)
harness = yaml.safe_load(pathlib.Path(options.harness).read_text())
if os.environ.get("FAKE_EXIT") or os.environ.get("FAKE_FAIL_APP") == harness["app"]:
    print("error: no_scope_compiled: every scope is not_compilable", file=sys.stderr)
    sys.exit(int(os.environ.get("FAKE_EXIT") or 1))
measured = pathlib.Path(options.harness).resolve().parent / "measured"
scoped = measured / "scoped"
scoped.mkdir(parents=True, exist_ok=True)
records, cases = [], []
for s in harness["scopes"]:
    ids = [f"scope:{s['id']}:{side}" for side in ("before", "after")]
    records.append({"id": s["id"], "function": s["function"], "language": s["language"], "current": s["current"],
                    "option": s["option"], "inputs": s["inputs"], "metrics": s["metrics"], "status": "measured",
                    "interop": {"check": "same_output", "result": "passed"}, "cases": ids})
    for case, base in zip(ids, (1000, 800)):
        cases.append({"id": case, "type": "Scope", "algorithm": s["function"], "provider": harness["app"],
                      "operation": case.rsplit(":", 1)[1], "inputSize": 1024, "keyKind": "none", "parameters": {},
                      "metrics": {"timeNs": {"iterations": 1, "runs": [base + d for d in (-2, -1, 0, 1, 2)]},
                                  "allocationCount": {"iterations": 1, "runs": [4, 4, 4]}}})
(scoped / "scoped-plan.yaml").write_text(yaml.safe_dump({"schemaVersion": 1, "app": harness["app"], "scopes": records}))
(scoped / "benchmark.json").write_text(json.dumps({"runtime": {}, "cases": cases}))
manifest = "schemaVersion: 1\nmode: device\n"
if os.environ.get("FAKE_ENERGY_INVALID"):
    (scoped / "energy.json").write_text(json.dumps({"cases": {
        cases[0]["id"]: {"valid": True, "invalid": []}, cases[1]["id"]: {"valid": False, "invalid": ["short_window"]}}}))
    manifest += "files:\n  energy: scoped/energy.json\n"
(measured / "manifest.yaml").write_text(manifest)
print(f"wrote:     {measured / 'manifest.yaml'}")
