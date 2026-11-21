"""The energy steps of pipeline.py --device: the run's one energy source and the guard around each energy step."""
from cryptobench.shared.device import timeouts
from cryptobench.shared.device.adb import DeviceError, DeviceLost
from cryptobench.shared.errors.line import one_line
from cryptobench.shared.log.warn import warn
from cryptobench.shared import paths

from cryptobench.stages.measurement.energy.sources import SOURCES
from cryptobench.stages.measurement.energy.sources.runner import Host
from cryptobench.shared.errors.failures import CommandError, EnergyError


def source(view, python, idle_seconds, stacktrace=False):
    """view: effective_view.EnergyView; idle_seconds: RunView.energy_idle_seconds. A capture the source cannot measure is refused here."""
    name = view.source
    adapter = SOURCES[name]
    unmeasured = sorted(view.captures - {"none"} - set(adapter.CAPTURES))
    if unmeasured:
        raise CommandError(f"not_supported: energy.source {name} captures {', '.join(unmeasured)}; it measures {', '.join(adapter.CAPTURES)}")
    return adapter(Host(python, stacktrace, paths.platform_tools(), timeouts.SECONDS["energy"]), idle_seconds)


def guarded(problems, step):
    """An energy step that fails costs this process its energy, never its timing: one warning, recorded."""
    try:
        step()
    except DeviceLost:
        raise
    except (EnergyError, DeviceError, timeouts.StepTimeout) as error:
        warn("energy_failed: " + one_line(error), problems)
