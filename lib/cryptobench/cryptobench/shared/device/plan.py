"""The device plan: pushed and AOT-compiled, prepared and skipped pulled back, the skips recorded so far, the per-run outputs cleared; a run's push with the
suppressErrors warning and the energy settle's files."""
from cryptobench.shared import paths
from cryptobench.shared.device.adb import PACKAGE, DeviceError
from cryptobench.shared.document.document import read_yaml
from cryptobench.shared.log.warn import warn


def push_plan(device, *files):
    device.push_files(*files)
    # Without androidx.benchmark's gradle plugin nothing AOT-compiles the APKs, and Jetpack fails
    # every case with NOT-AOT-COMPILED.
    for package in (PACKAGE, f"{PACKAGE}.test"):
        compiled = device.shell(f"cmd package compile -f -m speed {package}")
        if "Success" not in compiled:
            raise DeviceError(f"AOT compile {package}: {compiled.strip()}")


def plan_pulls(device, preparation):
    """(remote, local) of the prepared and skipped files."""
    return ((f"{device.files}/{paths.PREPARED}", paths.Preparation(preparation).prepared),
            (f"{device.files}/{paths.SKIPPED}", paths.Preparation(preparation).skipped))


def pull_plan(device, preparation):
    preparation.mkdir(parents=True, exist_ok=True)
    for remote, local in plan_pulls(device, preparation):
        device.pull(remote, local)


def recorded_skips(device, local):
    """The device's skipped.yaml pulled to local, as its document; empty when it cannot be pulled."""
    local.parent.mkdir(parents=True, exist_ok=True)
    return read_yaml(local) if device.pull_optional(f"{device.files}/{paths.SKIPPED}", local) else {}


def outputs(device, plan_files=()):
    """androidx's outputs and the plan directory's per-run files, so nothing of an earlier process is pulled as this one's."""
    return (f"{device.media}/*-benchmarkData.json", f"{device.media}/*.perfetto-trace", f"{device.media}/*.trace",
            *(f"{device.files}/{name}" for name in (*plan_files, paths.CPU_PINS)))


def clear_outputs(device, plan_files=()):
    device.shell(f"rm -f {' '.join(outputs(device, plan_files))}")


def push(device, options, plan, energy=None):
    """dex2oat runs in the AOT compile, so the energy settle comes after it, never before; energy.yaml follows the settle."""
    push_plan(device, *plan)
    if options.suppress_errors:
        warn(f"suppressErrors {options.suppress_errors}: these numbers are not comparable to an unsuppressed run")
    if energy:
        device.push_files(energy())
