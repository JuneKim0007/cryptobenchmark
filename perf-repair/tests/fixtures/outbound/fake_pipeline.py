import argparse, json, os, pathlib, sys

parser = argparse.ArgumentParser()
parser.add_argument("--config", required=True)
parser.add_argument("--results", required=True)
parser.add_argument("--bench", action="store_true")
parser.add_argument("--device", action="store_true")
options = parser.parse_args()
root = pathlib.Path(options.results)
root.mkdir(parents=True, exist_ok=True)
(root / "argv.json").write_text(json.dumps({"argv": sys.argv[1:], "cwd": os.getcwd()}))
for n in range(60):
    print(f"line {n}")
code = int(os.environ.get("FAKE_EXIT", "0"))
if code:
    print("error: fake failure", file=sys.stderr)
    sys.exit(code)
if not os.environ.get("FAKE_NO_MANIFEST"):
    mode = "device" if options.device else "host"
    folder = root / "fake-device"
    folder.mkdir(exist_ok=True)
    manifest = folder / "manifest.yaml"
    manifest.write_text(f"schemaVersion: 1\nmode: {mode}\nconfig: {options.config}\n")
    print(f"wrote:     {manifest}")
