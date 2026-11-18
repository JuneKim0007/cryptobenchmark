"""The energy steps of pipeline.py --device: capture selection and the run's one energy source."""
from cryptobench.shared.device import timeouts
from cryptobench.shared.device.adb import DeviceError, DeviceLost
from cryptobench.shared.errors.line import one_line
from cryptobench.shared.log.warn import warn
from cryptobench.shared import paths
from cryptobench.shared.settings.energy_capture import capture, source as source_of

from cryptobench.stages.measurement.energy.sources import SOURCES
from cryptobench.stages.measurement.energy.sources.runner import Host
from cryptobench.shared.document.document import read_yaml
from cryptobench.shared.errors.failures import EnergyError

__all__ = ["capture", "captures", "guarded", "source", "source_name"]


def _entries(document):
    for types in (document.get("providers") or {}).values():
        for names in types.values():
            for entry in names.values():
                yield from entry if isinstance(entry, list) else [entry]


def captures(effective):
    document = read_yaml(effective)
    default = capture(document.get("run"))
    return {capture(one, default) for one in _entries(document)} or {default}


def source_name(effective):
    """A session spans the whole run, and a run compares its cases: one source."""
    document = read_yaml(effective)
    default = source_of(document.get("run"))
    names = {source_of(one, default) for one in _entries(document)} or {default}
    if len(names) > 1:
        raise EnergyError(f"energy_sources_differ: {sorted(names)}; set harness.energy.source once, for the run")
    return names.pop()


def source(effective, python, stacktrace=False):
    return SOURCES[source_name(effective)](Host(python, stacktrace, paths.platform_tools(), timeouts.SECONDS["energy"]))


def guarded(problems, step):
    """An energy step that fails costs this process its energy, never its timing: one warning, recorded."""
    try:
        step()
    except DeviceLost:
        raise
    except (EnergyError, DeviceError, timeouts.StepTimeout) as error:
        warn("energy_failed: " + one_line(error), problems)
