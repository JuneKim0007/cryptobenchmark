"""The oracle steps of pipeline.py --interop: the plan's pairs on the host JVM or on the attached device."""
import shutil

from cryptobench.shared.device import gradle_runner, instrumentation
from cryptobench.shared import paths
from cryptobench.shared.device.adb import ONE_PASSED
from cryptobench.shared.device.plan import push_plan
from cryptobench.shared.document.document import read_yaml
from cryptobench.shared.settings import bundled


def stage_plan(plan, into):
    into.mkdir(parents=True, exist_ok=True)
    staged = paths.InteropFolder(into).plan
    if plan.resolve() != staged.resolve():
        shutil.copyfile(plan, staged)
    paths.InteropFolder(into).result.unlink(missing_ok=True)
    return staged


def on_host(effective, capture, trial, plan, out, stacktrace, stream):
    """The pairs on this JVM, the effective file's bundled providers installed first, as CheckKt does."""
    gradle_runner.run(f"{capture} {trial} {effective} {plan} {out}", stacktrace, stream, main_class="InteropKt",
                      properties=bundled.gradle_properties(bundled.recorded(effective)))


def on_device(device, waits, effective, capture, trial, plan, out):
    waits.retried(lambda: push_plan(device, effective, capture, trial, plan), "the plan push")
    result = f"{device.files}/{paths.INTEROP_RESULT}"
    instrumentation.run(device, waits, instrumentation.Instrumented("InteropCheck", cleared=(result,), passed=ONE_PASSED, pulled=((result, out),)))


def summary(out):
    pairs = read_yaml(out).get("pairs") or []
    counts = {}
    for pair in pairs:
        counts[pair["result"]] = counts.get(pair["result"], 0) + 1
        if pair["result"] != "pass":
            print(f"interop:   {pair['id']} {pair['group']} {pair['result']}: {pair['reason']}")
    print(f"interop:   {len(pairs)} pairs, " + ", ".join(f"{n} {result}" for result, n in sorted(counts.items())))
