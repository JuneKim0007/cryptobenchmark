"""What every device session of a run shares: its context, hooks, push, conversion and the files it records."""
import dataclasses, pathlib, time

import effective_view, gradle_runner
from device.adb import Device, measure_arguments
from energy_session import EnergySession
from session import clocks_hook, cooldown_hook, thermal_gate, thermal_hook
from stages.took import elapsed
from cryptobench import paths


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
    throttle_sleep: int | None = None
    cooldown: int = 0
    gate: object = None


def convert(run, arguments):
    """ConvertKt on one process; a case that did not get the samples it asked for is a problem the manifest records."""
    notices = []
    gradle_runner.run(arguments, run.options.stacktrace, run.options.stream, main_class="ConvertKt", notices=notices)
    run.problems.extend(line for line in notices if line.startswith("iterations_not_applied:"))


def gated(run, document):
    return dataclasses.replace(run, gate=thermal_gate.start(run.device, effective_view.thermal_gate(document)))


def session_arguments(run, document):
    return measure_arguments(run.options.suppress_errors, effective_view.metrics(document), run.throttle_sleep)


def pass_arguments(run, one):
    return tuple(measure_arguments(run.options.suppress_errors, one.metrics, run.throttle_sleep)) + one.arguments()


def timed_hooks(run, one, isolation):
    """The cool-down, then the gate, so a case's start temperature and clocks are read after both."""
    per_case = isolation == effective_view.CASE_ISOLATION
    gate = [thermal_gate.Gate(run.gate, run.device, one.label, per_case, run.problems)] if run.gate else []
    return [cooldown_hook.Cooldown(run.cooldown, one.label, per_case), *gate, clocks_hook.Clocks(run.device), thermal_hook.Thermal(run.device, one.label)]


def thermal_flag(process):
    reading = paths.Measurement(process.into).thermal
    return f" --thermal={reading}" if reading.is_file() else ""


def energy_preflight(options, source, session, discovery, files):
    started = time.monotonic()
    capability = source.preflight(session, discovery, options.energy_accept_unresponsive)
    files["energyCapability"] = capability
    elapsed("energy pre-flight and settle", started)
    return capability


def push(device, options, plan, energy=None):
    """dex2oat runs in the AOT compile, so the energy settle comes after it, never before; energy.yaml follows the settle."""
    device.push_plan(*plan)
    if options.suppress_errors:
        print(f"warning: suppressErrors {options.suppress_errors}: these numbers are not comparable to an unsuppressed run")
    if energy:
        device.push_files(energy())


def record(files, into, captures, device):
    if captures - {"none"} and paths.Measurement(into).energy.is_file():
        files.setdefault("energy", []).append(paths.Measurement(into).energy)
    if device and captures - {"dry"}:
        files.setdefault("clocks", []).append(paths.Measurement(into).clocks)
        if paths.Measurement(into).cpu_pins.is_file():
            files.setdefault("cpuPins", []).append(paths.Measurement(into).cpu_pins)
            import yaml
            for case, pin in (yaml.safe_load(paths.Measurement(into).cpu_pins.read_text()) or {}).items():
                if "failed" in pin:
                    print(f"warning: cpu_pin_failed: {case}: {pin['failed']}")


def singles(files, repetitions):
    for single in ("energy", "clocks", "cpuPins"):
        if single in files and repetitions == 1:
            files[single] = files[single][0]
