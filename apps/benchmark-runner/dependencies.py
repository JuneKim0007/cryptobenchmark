"""The host modules a run needs, checked before it starts: the first missing one is one coded line and exit 1.
Importing this file checks PyYAML and that cryptobench is this checkout's own, so it comes before any import that needs them. perf-repair's guide runs it as a command:

    dependencies.py [--config global.yaml] [--bench | --device]
"""
import argparse
import importlib.util
import pathlib
import subprocess
import sys

from failure import fail, reported

BASE = ("yaml", "cryptobench")
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


def _missing(module, python=sys.executable):
    """The coded line for a module that python cannot import, else None."""
    return None if _found(module, python) else f"missing_dependency: {module}; pip install -r requirements.txt"


def require(module, python=sys.executable):
    if line := _missing(module, python):
        raise CommandError(line)


def require_energy(source_name, python=sys.executable):
    require(ENERGY[source_name], python)


# CommandError needs cryptobench, so the import-time check stops the way an entry point does
for _module in BASE:
    if _line := _missing(_module):
        fail(_line)


def _loaded():
    return pathlib.Path(next(iter(importlib.util.find_spec("cryptobench").submodule_search_locations))).resolve()


def _outside_checkout(library):
    """The coded line for cryptobench loaded from another place than this checkout's library."""
    return (f"library_outside_checkout: cryptobench loads from {_loaded()}, not from this checkout's {library}; "
            "set PYTHONPATH to that folder or pip install -e it")


try:
    from cryptobench.shared import paths  # noqa: E402
except ModuleNotFoundError as error:
    # this checkout's library holds every module it imports, so a missing one is another library's
    if not (error.name or "").startswith("cryptobench."):
        raise
    fail(_outside_checkout("library (lib/cryptobench)"))
# this checkout is the one this file sits in; samefile, since macOS paths ignore case
_library = paths.repo(paths.checkout_of(__name__)).library.resolve()
if not any(folder.samefile(_library) for folder in _loaded().parents if _library.exists()):
    fail(_outside_checkout(_library))

from cryptobench.shared.errors.failures import CommandError  # noqa: E402
from cryptobench.shared.settings.energy_capture import capture, source  # noqa: E402
from global_file import global_config  # noqa: E402


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


if __name__ == "__main__":
    with reported():
        main()
