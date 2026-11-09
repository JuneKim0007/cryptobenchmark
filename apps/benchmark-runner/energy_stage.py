"""The energy steps of pipeline.py --device: capture selection and the run's one energy source."""
import sys

import yaml

import timeouts
from device.adb import DeviceError, android_home
from failure import one_line
from cryptobench import paths

paths.add_energy_imports()
from capture import capture, source as source_of  # noqa: E402
from sources import SOURCES  # noqa: E402
from sources.runner import EnergyError, Host  # noqa: E402

__all__ = ["EnergyError", "capture", "captures", "guarded", "source", "source_name"]


def _entries(document):
    for types in (document.get("providers") or {}).values():
        for names in types.values():
            for entry in names.values():
                yield from entry if isinstance(entry, list) else [entry]


def captures(effective):
    document = yaml.safe_load(effective.read_text())
    default = capture(document.get("run"))
    return {capture(one, default) for one in _entries(document)} or {default}


def source_name(effective):
    """A session spans the whole run, and a run compares its cases: one source."""
    document = yaml.safe_load(effective.read_text())
    default = source_of(document.get("run"))
    names = {source_of(one, default) for one in _entries(document)} or {default}
    if len(names) > 1:
        raise EnergyError(f"energy_sources_differ: {sorted(names)}; set harness.energy.source once, for the run")
    return names.pop()


def source(effective, python, stacktrace=False):
    return SOURCES[source_name(effective)](Host(python, stacktrace, android_home() / "platform-tools", timeouts.SECONDS["energy"]))


def guarded(problems, step):
    """An energy step that fails costs this process its energy, never its timing: one error line, recorded."""
    try:
        step()
    except (EnergyError, DeviceError, timeouts.StepTimeout) as error:
        line = "energy_failed: " + one_line(error)
        print(f"error: {line}", file=sys.stderr)
        problems.append(line)
