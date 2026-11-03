"""The energy steps of pipeline.py --device: capture selection and the run's one energy source."""
import json, pathlib, sys

import yaml

import timeouts
from device import DeviceError, android_home

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.append(str(ROOT / "tools/energy"))
from capture import capture, source as source_of  # noqa: E402
from sources import SOURCES  # noqa: E402
from sources.runner import EnergyError, Host  # noqa: E402

__all__ = ["EnergyError", "capture", "captures", "estimated_mark", "guarded", "source"]


def _entries(document):
    for types in (document.get("providers") or {}).values():
        for names in types.values():
            for entry in names.values():
                yield from entry if isinstance(entry, list) else [entry]


def captures(effective):
    document = yaml.safe_load(effective.read_text())
    default = capture(document.get("run"))
    return {capture(one, default) for one in _entries(document)} or {default}


def source(effective, python, stacktrace=False):
    """A session spans the whole run, and a run compares its cases: one source."""
    document = yaml.safe_load(effective.read_text())
    default = source_of(document.get("run"))
    names = {source_of(one, default) for one in _entries(document)} or {default}
    if len(names) > 1:
        raise EnergyError(f"energy_sources_differ: {sorted(names)}; set harness.energy.source once, for the run")
    return SOURCES[names.pop()](Host(python, stacktrace, android_home() / "platform-tools", timeouts.SECONDS["energy"]))


def estimated_mark(energy_files):
    """The manifest's mark of a run whose energy is estimated; a measured run has none."""
    paths = energy_files if isinstance(energy_files, list) else [energy_files] if energy_files else []
    documents = [json.loads(path.read_text()) for path in paths]
    sources = sorted({d["source"] for d in documents if d.get("kind") == "estimated"})
    return {"energy": {"source": ", ".join(sources), "kind": "estimated"}} if sources else {}


def guarded(problems, step):
    """An energy step that fails costs this process its energy, never its timing: one error line, recorded."""
    try:
        step()
    except (EnergyError, DeviceError, timeouts.StepTimeout) as error:
        line = "energy_failed: " + " ".join(str(error).split())[:500]
        print(f"error: {line}", file=sys.stderr)
        problems.append(line)
