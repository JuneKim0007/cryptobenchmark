"""An --interop run: perf-repair's pairs checked on the host JVM or the device, published beside or as the device folder."""
import pathlib, time

from cryptobench.shared.device.identity import capture_id
from cryptobench.shared.errors.failures import CommandError
from cryptobench.shared.results import layout as results_layout
from cryptobench.shared.results.manifest import add_to_manifest, manifest
from cryptobench.stages.verification import interop_oracle
from cryptobench.pipeline.took import elapsed
from cryptobench.shared import paths


def interop_run(options, configuration, device, root, shipped, discover_staged, located):
    """discover_staged and located are discovery's, passed in: the discovery runs inside this stage's staging folder."""
    plan = pathlib.Path(options.interop)
    if not (options.bench or device) or options.harness:
        raise CommandError("--interop: the pairs are checked on a --bench (host JVM) or a --device run, without --harness")
    if not plan.is_file():
        raise CommandError(f"missing_file: {plan} (--interop)")
    mode = "device" if device else "host"
    with results_layout.staged(root) as stage:
        _, effective, capture, trial, _ = discover_staged(options, configuration, device, root, stage, shipped)
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
        finished = paths.finished(results)
        if finished:
            results_layout.publish_beside(stage, results, paths.INTEROP)
        else:
            results_layout.publish(stage, results, options.discovery)
    interop = paths.RunTree(results).interop
    print(f"wrote:     {interop.result}")
    added = {"interopPlan": interop.plan, "interop": interop.result}
    if finished:
        add_to_manifest(results, added)
    else:
        manifest(results, mode, configuration, located(results, capture.name)[-1] | added)
    results_layout.report_superseded(results)
