"""A fake pipeline.py for the device stage: --identify, --probe, --bench, --device; each run is one line in <root>/runs.log
and its selection.exclude one in excluded.log.
The device folder is the recorded test-api36 results, each providers.bundled entry adding a provider named by its alias
or `create`, of the same primitives and MD5, measured like Fast; FAKE_INTERRUPT=1 fails after the old manifest is gone;
FAKE_VARIANTS=1 writes every case twice, `<id>_fixed` (Fast's runs times FIXED_SCALE) and `<id>_notFixed`, as the benchmark does, retried ids too;
FAKE_SELECT=1 keeps only the cases the config's test set and excludes select; FAKE_HEAL=1 also measures the recorded lost case;
FAKE_SCALE=<n> multiplies every timeNs run (anchors drift); FAKE_RENAME_CASES=1 renames every case but the healed one (no shared case); FAKE_FINGERPRINT=<text> is the runtime's build fingerprint."""
import argparse, fnmatch, hashlib, json, os, pathlib, shutil, sys

import yaml

RECORDED = pathlib.Path(__file__).resolve().parents[2] / "results" / "test-api36-00000000"
DEVICE_ID = os.environ.get("FAKE_DEVICE_ID", "fake-api36-00000000")

parser = argparse.ArgumentParser()
parser.add_argument("--config", required=True)
parser.add_argument("--results")
parser.add_argument("--discovery")
for flag in ("--bench", "--device", "--probe", "--identify"):
    parser.add_argument(flag, action="store_true")
options = parser.parse_args()


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True).encode()).hexdigest()


document = yaml.safe_load(pathlib.Path(options.config).read_text()) or {}
shipped = (document.get("providers") or {}).pop("bundled", None) or []
inputs = {"bundled": digest(shipped), "config": digest(document)}
if options.identify:
    print("identity:  " + json.dumps({"deviceId": DEVICE_ID, "mode": "device" if options.device else "host",
                                      "config": options.config, "inputs": inputs,
                                      "harness": os.environ.get("FAKE_HARNESS", "fake-harness")}))
    sys.exit(0)

root = pathlib.Path(options.results)
with open(root / "runs.log", "a") as log:
    log.write(" ".join(sys.argv[1:]) + "\n")
excluded = sorted(f"{r['type']}|{r['name']}|{r['provider']}" for r in (document.get("selection") or {}).get("exclude") or [])
with open(root / "excluded.log", "a") as log:
    log.write(json.dumps(excluded) + "\n")
folder = root / DEVICE_ID
(folder / "manifest.yaml").unlink(missing_ok=True)
if os.environ.get("FAKE_INTERRUPT"):
    print("error: interrupted", file=sys.stderr)
    sys.exit(1)
for item in RECORDED.iterdir():
    if item.name != "manifest.yaml":
        target = folder / item.name
        shutil.copytree(item, target, dirs_exist_ok=True) if item.is_dir() else shutil.copy(item, target)
manifest = yaml.safe_load((RECORDED / "manifest.yaml").read_text())
ADDED = (("Cipher", "AES/GCM/NoPadding"), ("MessageDigest", "SHA-256"), ("MessageDigest", "MD5"))
probe_path, trial_path = folder / manifest["files"]["probe"], folder / manifest["files"]["trial"]
probe, trial = yaml.safe_load(probe_path.read_text()), yaml.safe_load(trial_path.read_text())
for n, entry in enumerate(shipped):
    name = entry.get("alias") or entry["create"]
    services = [{"type": t, "algorithm": a, "className": f"{name}.{i}"} for i, (t, a) in enumerate(ADDED)]
    probe["providers"].append({"name": name, "version": "1", "precedence": 3 + n, "origin": "bundled", "usable": True,
                               "artifact": entry["artifact"],
                               "services": services})
    trial["services"] += [{"provider": name, "type": t, "algorithm": a, "instantiates": True,
                           "defaultRun": {"works": True, "inputSize": 1024}} for t, a in ADDED]
bench_path = folder / "benchmark" / "benchmark.json"
bench = json.loads(bench_path.read_text())
for entry in shipped:
    name = entry.get("alias") or entry["create"]
    bench["cases"] += [{**c, "id": f"{c['id']}_{name}", "provider": name} for c in list(bench["cases"])
                       if (c["type"], c["algorithm"]) in ADDED and c["provider"] == "Fast"]


def _matches(rule, case):
    name = rule.get("name")
    return (rule.get("provider") in (None, case["provider"]) and rule.get("type") in (None, case["type"])
            and (name is None or fnmatch.fnmatch(case["algorithm"].upper(), name.upper())))


def selected(cases):
    """The real selection's outcome for these fixture names: included by the test set, excluded by neither list."""
    named = pathlib.Path((document.get("selection") or {}).get("testSet", ""))
    path = named if named.is_absolute() else pathlib.Path(options.config).parent / named
    test_set = yaml.safe_load(path.read_text()) or {}
    excludes = (test_set.get("exclude") or []) + ((document.get("selection") or {}).get("exclude") or [])
    include = test_set.get("include") or []
    return [c for c in cases if (not include or any(_matches(r, c) for r in include)) and not any(_matches(r, c) for r in excludes)]


if os.environ.get("FAKE_HEAL"):
    bench["cases"] += [{**c, "id": "d_slow", "provider": "Slow"} for c in list(bench["cases"]) if c["id"] == "d_fast"]
if os.environ.get("FAKE_SCALE"):
    for c in bench["cases"]:
        c["metrics"]["timeNs"]["runs"] = [r * float(os.environ["FAKE_SCALE"]) for r in c["metrics"]["timeNs"]["runs"]]
if os.environ.get("FAKE_FINGERPRINT"):
    bench["runtime"]["fingerprint"] = os.environ["FAKE_FINGERPRINT"]
if os.environ.get("FAKE_RENAME_CASES"):
    bench["cases"] = [{**c, "id": c["id"] if c["id"] == "d_slow" else c["id"] + "_override"} for c in bench["cases"]]
if os.environ.get("FAKE_SELECT"):
    bench["cases"] = selected(bench["cases"])
FIXED_SCALE = 4
PER_CALL = {"fixed": "initAndOperation", "notFixed": "getInstanceInitAndOperation"}


def scaled(case):
    metrics = {k: {**v, "runs": [r * FIXED_SCALE for r in v["runs"]]} if k == "timeNs" and case["provider"] == "Fast" else v
               for k, v in case["metrics"].items()}
    return {**case, "metrics": metrics}


def both(case, variant):
    """The key right after keyKind, as the benchmark writes it."""
    keyed = list({**case, "id": f"{case['id']}_{variant}"}.items())
    at = [k for k, _ in keyed].index("keyKind") + 1
    out = dict(keyed[:at] + [("variant", variant)] + keyed[at:])
    return scaled(out) if variant == "fixed" else out


if os.environ.get("FAKE_VARIANTS"):
    bench["cases"] = [both(c, v) for c in bench["cases"] for v in ("fixed", "notFixed")]
bench_path.write_text(json.dumps(bench))
prepared_path = folder / "preparation" / "prepared.yaml"
prepared = yaml.safe_load(prepared_path.read_text())
for entry in shipped:
    name = entry.get("alias") or entry["create"]
    prepared["cases"] += [{**c, "id": f"{c['id']}_{name}", "provider": name} for c in list(prepared["cases"])
                          if (c["type"], c["algorithm"]) in ADDED and c["provider"] == "Fast"]
if os.environ.get("FAKE_VARIANTS"):
    prepared["cases"] = [{**c, "id": f"{c['id']}_{v}", "variant": v, "perCall": PER_CALL[v]}
                         for c in prepared["cases"] for v in ("fixed", "notFixed")]
if os.environ.get("FAKE_SELECT"):
    prepared["cases"] = selected(prepared["cases"])
prepared_path.write_text(yaml.safe_dump(prepared, sort_keys=False))
probe_path.write_text(yaml.safe_dump(probe, sort_keys=False))
trial_path.write_text(yaml.safe_dump(trial, sort_keys=False))
if os.environ.get("FAKE_VARIANTS"):
    manifest["retried"] = [f"{c}_{v}" for c in manifest.get("retried") or [] for v in ("fixed", "notFixed")]
manifest.update(deviceId=DEVICE_ID, mode="device" if options.device else "host", config=options.config, inputs=inputs)
if os.environ.get("FAKE_FINGERPRINT"):
    manifest["runtime"] = {**manifest["runtime"], "fingerprint": os.environ["FAKE_FINGERPRINT"]}
if options.probe:
    manifest["files"] = {k: manifest["files"][k] for k in ("probe", "trial", "inventory", "effective")}
    manifest["counts"] = {}
(folder / "manifest.yaml").write_text(yaml.safe_dump(manifest, sort_keys=False))
print(f"wrote:     {folder / 'manifest.yaml'}")
