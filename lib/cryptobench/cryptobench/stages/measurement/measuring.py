"""What every device session of a run shares: its context, hooks, conversion and the files it records."""
import dataclasses, pathlib, shutil, time

from cryptobench.shared.device import gradle_runner
from cryptobench.shared.device.adb import NO_DEFAULT_PROFILER, Device
from cryptobench.stages.measurement.energy.session import EnergySession
from cryptobench.shared.device import reconnect
from cryptobench.stages.measurement import thermal
from cryptobench.stages.measurement.session import clocks_hook, cooldown_hook, dynamic_temperature, thermal_hook
from cryptobench.pipeline.took import elapsed
from cryptobench.shared.log.warn import warn
from cryptobench.shared.errors.line import one_line
from cryptobench.shared import paths
from cryptobench.shared.document.document import read_yaml
from cryptobench.shared.document.dump import dump_yaml
from cryptobench.shared.document.write import write_text

THROTTLE_SLEEP = "androidx.benchmark.thermalThrottle.sleepDurationSeconds"
IDLE_GATE, START_IDLE, END_IDLE = "energy idle", "the start idle reading", "the end idle reading"
SPAN_SHARE = 0.9  # an idle trace whose samples span less of its configured length is recorded


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
    # dynamic_temperature.opened's gate, run.launchRetries, reconnect.Reconnect
    gate: object
    retries: int
    reconnect: object
    # the device folder and the run's record (shared/results/run_record.py), whose run block each pass's Expectation reads
    unit: pathlib.Path
    record: dict


def convert(run, arguments, problems=None):
    """ConvertKt on one process; a case that did not get the samples it asked for is a problem the manifest records (problems, when given, instead)."""
    notices = []
    gradle_runner.run(arguments, run.options.stacktrace, run.options.stream, main_class="ConvertKt", notices=notices)
    (run.problems if problems is None else problems).extend(line for line in notices if line.startswith("iterations_not_applied:"))


def gate_opened(device, document, problems, waits):
    return waits.retried(lambda: dynamic_temperature.opened(device, document, problems), "the thermal gate's start")


def measure_arguments(suppress, throttle_sleep=None):
    return (NO_DEFAULT_PROFILER + (["-e", "androidx.benchmark.suppressErrors", suppress] if suppress else [])
            + (["-e", THROTTLE_SLEEP, str(throttle_sleep)] if throttle_sleep is not None else []))


def pull_pins(device, process):
    """The per-case core pins a timed process writes beside its results; a redo keeps the pins of the cases it did not launch again."""
    pins = paths.Measurement(process.into).cpu_pins
    kept = process.earlier(pins, key=None)
    pins.unlink(missing_ok=True)
    device.pull_optional(f"{device.files}/{paths.CPU_PINS}", pins)
    if kept:
        write_text(pins, dump_yaml(kept | ((read_yaml(pins) or {}) if pins.is_file() else {})))


def session_arguments(run):
    return measure_arguments(run.options.suppress_errors, run.throttle_sleep)


def pass_arguments(run, one, samples=None):
    return tuple(measure_arguments(run.options.suppress_errors, run.throttle_sleep)) + one.arguments(samples)


def timed_hooks(run, one, gate):
    """The gate holds in the launch loop, before these; Thermal writes its history into thermal.json."""
    return [cooldown_hook.Cooldown(one.cooldown, one.label), clocks_hook.Clocks(run.device), thermal_hook.Thermal(run.device, one.label, gate.history)]


def thermal_flag(process):
    reading = paths.Measurement(process.into).thermal
    return f" --thermal={reading}" if reading.is_file() else ""


def skin(device):
    reading = thermal.poll(device).skin
    return {"sensor": reading[0], "celsius": reading[1]} if reading else None


def idle_held(run, reading, gate):
    """An idle reading waits behind the energy pass's gate scope (passes.Pass.gate); the skin temperature at its start and end goes to energy.yaml."""
    def held(record):
        run.gate.session(IDLE_GATE, gate).hold(reading)
        start = skin(run.device)
        record()
        return {"start": start, "end": skin(run.device)}
    return held


def idle_span(problems, capability, key, reading):
    document = read_yaml(capability) or {}
    span, seconds = document.get(f"{key}SpanSeconds"), document.get(f"{key}WindowSeconds")
    if span is not None and span < SPAN_SHARE * seconds:
        warn(f"idle_span_short: {reading}: rail samples span {span:.1f} of {seconds} s; idle power is over the span", problems)


def energy_preflight(run, gate):
    started = time.monotonic()
    capability = run.source.preflight(run.session, run.discovery, run.options.energy_accept_unresponsive, idle_held(run, START_IDLE, gate))
    run.files["energyCapability"] = capability
    idle_span(run.problems, capability, "idle", START_IDLE)
    elapsed("energy pre-flight", started)
    return capability


def energy_end(run, redo, gate):
    """After the last pass: the end idle reading, then each process's energy again over the line between the two readings.
    redo holds (pass, process folder, step) per process this run measured with an energy.json; a step writes into the process's staging folder
    and returns (staged, kept) file pairs, swapped in only once every step succeeded. Returns {pass: the folders converted again}.
    Any failure leaves every energy.json on the start reading (idle_start_only), recorded, and the run goes on."""
    started = time.monotonic()
    try:
        ended = run.reconnect.retried(lambda: run.source.idle_end(run.session, run.discovery, idle_held(run, END_IDLE, gate)), "the end idle reading")
    except Exception as error:  # hours of measured data stand on the start reading rather than stop here
        warn(f"energy_failed: {END_IDLE}: {one_line(error) or type(error).__name__}", run.problems)
        warn("idle_start_only: no end idle reading; energy.json keeps the start reading alone", run.problems)
        return {}
    if not ended:
        return {}
    idle_span(run.problems, paths.Discovery(run.discovery).energy, "idleEnd", END_IDLE)
    print(f"idle:      energy again for {len(redo)} process{'es' if len(redo) != 1 else ''} over the interpolated idle")
    swaps, redone = [], {}
    try:
        for one, into, step in redo:
            staging = paths.Measurement(into).redo
            shutil.rmtree(staging, ignore_errors=True)
            staging.mkdir(parents=True)
            swaps += step()
            if missing := [str(staged) for staged, _ in swaps if not staged.is_file()]:
                raise FileNotFoundError(f"missing_file: {', '.join(missing)}")
            redone.setdefault(one, []).append(into)
    except Exception as error:  # one process failing leaves none redone: the run never mixes the two baselines
        warn(f"energy_failed: energy again: {one_line(error) or type(error).__name__}", run.problems)
        warn("idle_start_only: energy again failed; every energy.json keeps the start reading alone", run.problems)
        return {}
    else:
        for staged, kept in swaps:
            staged.replace(kept)
    finally:
        for _, into, _ in redo:
            shutil.rmtree(paths.Measurement(into).redo, ignore_errors=True)
    elapsed("energy end idle", started)
    return redone


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
    for single in ("energy", "clocks", "cpuPins", "energySamples"):
        if single in files and repetitions == 1:
            files[single] = files[single][0]
