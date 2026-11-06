"""A fake `pipeline.py --device --harness`: every harness scope compiled and interop passed; --identify names FAKE_HARNESS.
FAKE_EXIT fails every run, FAKE_FAIL_APP only the app of that name."""
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
checked = pathlib.Path(options.harness).resolve().parent / "checked"
scoped = checked / "scoped"
scoped.mkdir(parents=True, exist_ok=True)
records = [{"id": s["id"], "function": s["function"], "language": s["language"], "current": s["current"],
            "option": s["option"], "inputs": s["inputs"], "status": "checked",
            "interop": {"check": "same_output", "result": "passed"}} for s in harness["scopes"]]
(scoped / "scoped-plan.yaml").write_text(yaml.safe_dump({"schemaVersion": 1, "app": harness["app"], "scopes": records}))
(checked / "manifest.yaml").write_text("schemaVersion: 1\nmode: device\n")
print(f"wrote:     {checked / 'manifest.yaml'}")
