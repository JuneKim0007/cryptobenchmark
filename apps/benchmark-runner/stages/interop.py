"""An --interop run: perf-repair's pairs checked on the host JVM or the device, published beside or as the device folder."""
import pathlib, time

from device.identity import capture_id
from failure import fail
from results import layout as results_layout
from results.manifest import add_to_manifest, manifest
from stages import interop_oracle
from stages.discover import discover_staged, located
from stages.took import elapsed
from cryptobench import paths


def interop_run(options, configuration, device, root):
    plan = pathlib.Path(options.interop)
    if not (options.bench or device) or options.harness:
        fail("--interop: the pairs are checked on a --bench (host JVM) or a --device run, without --harness")
    if not plan.is_file():
        fail(f"missing_file: {plan} (--interop)")
    mode = "device" if device else "host"
    with results_layout.staged(root) as stage:
        _, effective, capture, trial, _ = discover_staged(options, configuration, device, root, stage)
        staged_plan = interop_oracle.stage_plan(plan, paths.RunTree(stage).interop.root)
        out = paths.InteropFolder(staged_plan.parent).result
        started = time.monotonic()
        if device:
            interop_oracle.on_device(device, effective, capture, trial, staged_plan, out)
        else:
            interop_oracle.on_host(capture, trial, staged_plan, out, options.stacktrace, options.stream)
        elapsed("interop check", started)
        interop_oracle.summary(out)
        results = root / capture_id(capture)
        finished = paths.RunTree(results).manifest.is_file()
        if finished:
            results_layout.publish_interop(stage, results)
        else:
            results_layout.publish(stage, results, options.discovery)
    interop = paths.RunTree(results).interop
    print(f"wrote:     {interop.result}")
    added = {"interopPlan": interop.plan, "interop": interop.result}
    if finished:
        add_to_manifest(results, added)
    else:
        manifest(results, mode, configuration, located(results, capture.name)[-1] | added)
