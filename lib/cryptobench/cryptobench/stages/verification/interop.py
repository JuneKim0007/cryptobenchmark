"""An --interop run: perf-repair's pairs checked on the host JVM or the device, published beside or as the device folder."""
import pathlib, time

from cryptobench.shared.device import reconnect
from cryptobench.shared.errors.failures import CommandError
from cryptobench.shared.results import layout as results_layout
from cryptobench.shared.results.publish_unit import Route, publish_unit
from cryptobench.stages.verification import interop_oracle
from cryptobench.pipeline.took import elapsed
from cryptobench.shared import paths

INTEROP = Route(paths.INTEROP, lambda tree: {"interopPlan": tree.interop.plan, "interop": tree.interop.result})


def interop_run(options, configuration, device, root, shipped, discover_staged, located, suite=None):
    """discover_staged and located are discovery's, passed in: the discovery runs inside this stage's staging folder."""
    plan = pathlib.Path(options.interop)
    if not (options.bench or device) or options.harness:
        raise CommandError("--interop: the pairs are checked on a --bench (host JVM) or a --device run, without --harness")
    if not plan.is_file():
        raise CommandError(f"missing_file: {plan} (--interop)")
    with results_layout.staged(root) as stage:
        found = discover_staged(options, configuration, device, root, stage, shipped, suite)
        effective, capture, trial = found.effective, found.capture, found.trial
        staged_plan = interop_oracle.stage_plan(plan, paths.RunTree(stage).interop.root)
        out = paths.InteropFolder(staged_plan.parent).result
        started = time.monotonic()
        if device:
            interop_oracle.on_device(device, reconnect.Reconnect.of(device, options), effective, capture, trial, staged_plan, out)
        else:
            interop_oracle.on_host(capture, trial, staged_plan, out, options.stacktrace, options.stream)
        elapsed("interop check", started)
        interop_oracle.summary(out)
        publish_unit(root, stage, found, INTEROP, mode="device" if device else "host", configuration=configuration,
                     discovery_mode=options.discovery, located=located, suite=suite)
