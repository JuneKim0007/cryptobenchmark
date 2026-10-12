"""Stands in for cryptobenchmark's scripts/pipeline.py: records its arguments, writes a manifest.

FAKE_EXIT=<n> exits n after printing; FAKE_NO_MANIFEST=1 exits 0 without writing the manifest.
"""
import argparse, json, os, pathlib, sys

parser = argparse.ArgumentParser()
parser.add_argument("--config", required=True)
parser.add_argument("--results", required=True)
parser.add_argument("--bench", action="store_true")
parser.add_argument("--device", action="store_true")
options = parser.parse_args()
results = pathlib.Path(options.results)
results.mkdir(parents=True, exist_ok=True)
(results / "argv.json").write_text(json.dumps({"argv": sys.argv[1:], "cwd": os.getcwd()}))
for n in range(60):
    print(f"line {n}")
code = int(os.environ.get("FAKE_EXIT", "0"))
if code:
    print("error: fake failure", file=sys.stderr)
    sys.exit(code)
if not os.environ.get("FAKE_NO_MANIFEST"):
    mode = "device" if options.device else "host"
    (results / "manifest.yaml").write_text(f"schemaVersion: 1\nmode: {mode}\nconfig: {options.config}\n")
