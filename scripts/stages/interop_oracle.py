"""The oracle steps of pipeline.py --interop: the plan's pairs on the host JVM or on the attached device."""
import shutil

import yaml

import gradle_runner
from device.adb import ONE_PASSED, DeviceError, instrumentation_report

PLAN = "interop_plan.yaml"   # InteropPlanFile.NAME
RESULT = "interop.yaml"      # InteropFile.NAME


def stage_plan(plan, into):
    into.mkdir(parents=True, exist_ok=True)
    staged = into / PLAN
    if plan.resolve() != staged.resolve():
        shutil.copyfile(plan, staged)
    (into / RESULT).unlink(missing_ok=True)
    return staged


def on_host(capture, trial, plan, out, stacktrace, stream):
    gradle_runner.run("quick-bench", f"{capture} {trial} {plan} {out}", stacktrace, stream, main_class="InteropKt")


def on_device(device, effective, capture, trial, plan, out):
    device.shell(f"rm -f {device.files}/{RESULT}")
    device.run("push", str(effective), str(capture), str(trial), str(plan), f"{device.files}/")
    output = device.instrument("InteropCheck")
    if not ONE_PASSED.search(output):
        raise DeviceError("InteropCheck failed on the device:\n" + instrumentation_report(output))
    device.pull(f"{device.files}/{RESULT}", out)


def summary(out):
    pairs = (yaml.safe_load(out.read_text()) or {}).get("pairs") or []
    counts = {}
    for pair in pairs:
        counts[pair["result"]] = counts.get(pair["result"], 0) + 1
        if pair["result"] != "pass":
            print(f"interop:   {pair['id']} {pair['group']} {pair['result']}: {pair['reason']}")
    print(f"interop:   {len(pairs)} pairs, " + ", ".join(f"{n} {result}" for result, n in sorted(counts.items())))
