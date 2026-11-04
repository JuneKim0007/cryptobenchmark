"""The host modules a run needs, checked before it starts: the first missing one is one coded line and exit 1.
Importing this file checks PyYAML, so it comes before any import that needs it. perf-repair's guide runs it as a command:

    dependencies.py [--config global.yaml] [--bench | --device]
"""
import argparse
import importlib.util
import pathlib
import subprocess
import sys

from failure import fail
from global_file import global_config
from repo import ROOT

sys.path.append(str(ROOT / "tools/energy"))
from capture import capture, source

BASE = ("yaml",)
ANALYSIS = "matplotlib"
ENERGY = {"rails": "perfetto", "manafa": "manafa"}
ENERGY_CAPTURES = ("measured", "dry")


def _found(module, python=sys.executable):
    if python == sys.executable:
        return importlib.util.find_spec(module) is not None
    probe = f"import importlib.util, sys; sys.exit(importlib.util.find_spec({module!r}) is None)"
    try:
        return subprocess.run([python, "-c", probe], capture_output=True, check=False).returncode == 0
    except OSError:
        return False


def require(module, python=sys.executable):
    if not _found(module, python):
        fail(f"missing_dependency: {module}; pip install -r requirements.txt")


def require_energy(source_name, python=sys.executable):
    require(ENERGY[source_name], python)


def _run_of(configuration):
    import yaml
    return (yaml.safe_load(pathlib.Path(configuration).read_text()) or {}).get("run")


def check(options, configuration):
    """Only what this run reaches: analysis on a plain timed run, the energy source's module when the config captures."""
    if options.probe or options.identify or options.interop or not (options.bench or options.device):
        return
    run = _run_of(configuration)
    captured = capture(run)
    if not options.harness and captured != "dry":
        require(ANALYSIS)
    if options.device and captured in ENERGY_CAPTURES:
        require_energy(source(run), options.energy_python)


def main():
    parser = argparse.ArgumentParser(description="the modules a pipeline.py run would need")
    parser.add_argument("--config")
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--bench", action="store_true")
    mode.add_argument("--device", action="store_true")
    options = parser.parse_args()
    options.probe = options.identify = options.interop = options.harness = None
    options.energy_python = sys.executable
    check(options, global_config(options.config))


for _module in BASE:
    require(_module)

if __name__ == "__main__":
    main()
