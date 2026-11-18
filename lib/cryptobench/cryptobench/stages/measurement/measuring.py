"""What every device session of a run shares: its context, hooks, conversion and the files it records."""
import dataclasses, pathlib, time

from cryptobench.shared.settings import effective_view
from cryptobench.shared.device import gradle_runner
from cryptobench.shared.device.adb import NO_DEFAULT_PROFILER, Device
from cryptobench.stages.measurement.energy.session import EnergySession
from cryptobench.stages.measurement.session import clocks_hook, cooldown_hook, dynamic_temperature, thermal_hook
from cryptobench.pipeline.took import elapsed
from cryptobench.shared.log.warn import warn
from cryptobench.shared import paths
from cryptobench.shared.document.document import read_yaml

THROTTLE_SLEEP = "androidx.benchmark.thermalThrottle.sleepDurationSeconds"


@dataclasses.dataclass(frozen=True)
class Measuring:
    """What every device session of a run shares: the device, the energy source, the run's options, files and problems."""
    device: Device
    session: EnergySession
    source: object
    options: object
    discovery: pathlib.Path
    files: dict
    problems: list
    # variant_order.chosen's order for run.orderSeed
    order: object
    # None keeps Jetpack's own sleep (effective_view.throttle_sleep)
    throttle_sleep: int | None
    cooldown: int
    # dynamic_temperature.opened's gate, run.launchRetries, reconnect.Reconnect
    gate: object
    retries: int
    reconnect: object


def convert(run, arguments):
    """ConvertKt on one process; a case that did not get the samples it asked for is a problem the manifest records."""
    notices = []
    gradle_runner.run(arguments, run.options.stacktrace, run.options.stream, main_class="ConvertKt", notices=notices)
    run.problems.extend(line for line in notices if line.startswith("iterations_not_applied:"))


def gate_opened(device, document, problems, waits):
    return waits.retried(lambda: dynamic_temperature.opened(device, document, problems), "the thermal gate's start")


def measure_arguments(suppress, throttle_sleep=None):
    return (NO_DEFAULT_PROFILER + (["-e", "androidx.benchmark.suppressErrors", suppress] if suppress else [])
            + (["-e", THROTTLE_SLEEP, str(throttle_sleep)] if throttle_sleep is not None else []))


def pull_pins(device, into):
    """The per-case core pins a timed process writes beside its results."""
    paths.Measurement(into).cpu_pins.unlink(missing_ok=True)
    device.pull_optional(f"{device.files}/{paths.CPU_PINS}", paths.Measurement(into).cpu_pins)


def session_arguments(run):
    return measure_arguments(run.options.suppress_errors, run.throttle_sleep)


def pass_arguments(run, one):
    return tuple(measure_arguments(run.options.suppress_errors, run.throttle_sleep)) + one.arguments()


def timed_hooks(run, one, gate):
    """The gate holds in the launch loop, before these; Thermal writes its history into thermal.json."""
    return [cooldown_hook.Cooldown(run.cooldown, one.label), clocks_hook.Clocks(run.device), thermal_hook.Thermal(run.device, one.label, gate.history)]


def thermal_flag(process):
    reading = paths.Measurement(process.into).thermal
    return f" --thermal={reading}" if reading.is_file() else ""


def energy_preflight(options, source, session, discovery, files):
    started = time.monotonic()
    capability = source.preflight(session, discovery, options.energy_accept_unresponsive)
    files["energyCapability"] = capability
    elapsed("energy pre-flight and settle", started)
    return capability


def record(files, into, captures, device):
    if captures - {"none"} and paths.Measurement(into).energy.is_file():
        files.setdefault("energy", []).append(paths.Measurement(into).energy)
    if device and captures - {"dry"}:
        files.setdefault("clocks", []).append(paths.Measurement(into).clocks)
        if paths.Measurement(into).cpu_pins.is_file():
            files.setdefault("cpuPins", []).append(paths.Measurement(into).cpu_pins)
            for case, pin in (read_yaml(paths.Measurement(into).cpu_pins)).items():
                if "failed" in pin:
                    warn(f"cpu_pin_failed: {case}: {pin['failed']}")


def singles(files, repetitions):
    for single in ("energy", "clocks", "cpuPins"):
        if single in files and repetitions == 1:
            files[single] = files[single][0]
