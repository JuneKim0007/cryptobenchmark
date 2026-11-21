"""One measuring session on the device: processes over repetitions, an instrumentation process per case, and hooks around the session,
each process and each case."""
import dataclasses, pathlib, re

from cryptobench.shared.device import timeouts
from cryptobench.shared.errors.failures import ALL_CASES_SKIPPED, AllSkipped
from cryptobench.shared.errors.line import one_line
from cryptobench.stages.measurement import case_files
from cryptobench.shared.device import reconnect
from cryptobench.stages.measurement.session import blocks, case_isolation, launch, skips
from cryptobench.stages.measurement.validation import rejected, rules
from cryptobench.shared.device.adb import DeviceError, DeviceLost
from cryptobench.shared.device.plan import clear_outputs
from cryptobench.shared import paths
from cryptobench.shared.log.warn import warn
from cryptobench.shared.document.document import read_yaml

COUNTED = re.compile(r"^Tests run: (\d+),\s+Failures: (\d+)", re.M)


@dataclasses.dataclass(frozen=True)
class Plan:
    test_class: str
    arguments: tuple
    # (repetition, listed cases) -> the launch order (variant_order.chosen)
    order: object
    # the pass's dynamic_temperature gate, run.launchRetries, the run's reconnect.Reconnect
    gate: object
    retries: int
    reconnect: object
    # the device folder, whose rejected/ takes a failed attempt; the pass's validation/expectation.Expectation
    unit: pathlib.Path
    expectation: object
    timed: bool = True
    cleared: tuple = ()
    stale: tuple = ()
    pull_plan: object = lambda _process: None
    after_process: object = lambda _process: None
    # the pass's blocks.Blocks; None measures every repetition and records nothing
    blocks: object = None
    kept: object = lambda _process: None
    # a failed case's final skip code from the device's skipped.yaml (skips.py); None: an ordinary failure
    refused: object = lambda _case: None
    # the pass's window.MinWindow; None keeps the configured samples
    sizing: object = None
    # the device's prepared.yaml and skipped.yaml pulled; the skipped.yaml document (a refused listing reads it)
    plan_skips: object = lambda: {}


@dataclasses.dataclass
class Process:
    repetition: int
    into: pathlib.Path
    cases: list = dataclasses.field(default_factory=list)
    failures: list = dataclasses.field(default_factory=list)
    start_reading: object = None
    end_reading: object = None
    # what plan.sizing recorded per case: energy-samples.yaml
    samples: dict = dataclasses.field(default_factory=dict)
    # {case, attempt, code} per launch again: the block record's relaunched
    relaunched: list = dataclasses.field(default_factory=list)
    # {case: [Finding]}: a kept run's cases a restart launches again; empty measures every case
    redo: dict = dataclasses.field(default_factory=dict)
    # the kept run's recorded problem lines, so its given-up cases stay given up
    recorded: tuple = ()

    def earlier(self, path, key="cases"):
        """A redo's per-case entries of a file the process rewrites, for the cases not launched again; {} otherwise."""
        if not self.redo or not path.is_file():
            return {}
        document = read_yaml(path)
        entries = document.get(key) if key else document
        return {case: entry for case, entry in (entries or {}).items() if case not in self.redo}

    @property
    def data(self):
        return paths.Measurement(self.into).data


class Hooks:
    """No-op steps; a hook overrides those it needs. after_* run in reverse order, so hooks nest like contexts."""

    def before_session(self):
        pass

    def before_process(self, process):
        pass

    def before_case(self, process, case):
        pass

    def after_case(self, process, case, failure):
        pass

    def after_process(self, process):
        pass

    def abandon(self, process):
        pass

    def after_session(self, processes):
        pass


def process_folder(root, repetition, repetitions):
    return root if repetitions == 1 else paths.Measurement(root).process(repetition).root


def process_line(repetition, repetitions):
    if repetitions > 1:
        print(f"process:   {repetition} of {repetitions}")


def run_session(device, plan, repetitions, hooks, folder, problems):
    """folder(repetition) is the process's folder; a case that failed is one problem line, a process that measured none the run's failure. A block an
    earlier run recorded is not measured again: its processes go through plan.kept."""
    for hook in hooks:
        hook.before_session()
    processes = []

    def measured(repetition):
        processes.append(one_process(device, plan, Process(repetition, folder(repetition)), hooks, repetitions, problems))
        return processes[-1].relaunched
    if plan.blocks is None:
        for repetition in range(1, repetitions + 1):
            measured(repetition)
    else:
        def redone(repetition, failed, lines):
            processes.append(one_process(device, plan, Process(repetition, folder(repetition), redo=failed, recorded=lines), hooks, repetitions, problems))
            return processes[-1].relaunched
        blocks.measured(plan.blocks, folder, measured, lambda repetition: plan.kept(Process(repetition, folder(repetition))), redone, problems)
    for hook in reversed(hooks):
        hook.after_session(processes)
    return processes


def one_process(device, plan, process, hooks, repetitions, problems):
    process_line(process.repetition, repetitions)
    process.into.mkdir(parents=True, exist_ok=True)
    started = []
    try:
        # a hook that fails here may have opened part of its step, so it is abandoned with those before it
        for hook in hooks:
            started.append(hook)
            plan.reconnect.retried(lambda hook=hook: hook.before_process(process), f"{type(hook).__name__}.before_process")
        if plan.timed:
            measure(device, plan, process, hooks)
            plan.reconnect.retried(lambda: plan.pull_plan(process), "the plan pull")
            completed(device, plan, process, hooks)
    except BaseException as error:
        # the interrupt kills adb, not the test it started on the device
        if isinstance(error, KeyboardInterrupt):
            stopped(device)
        for hook in reversed(started):
            hook.abandon(process)
        if plan.timed:
            salvaged(plan, process)
        problems += process.failures
        raise
    problems += process.failures
    failed = closed(process, hooks, plan.reconnect)
    plan.after_process(process)
    if failed:
        raise failed
    return process


def salvaged(plan, process):
    """A stopped process still brings back what the device prepared and skipped, so its partial run can be read."""
    try:
        plan.pull_plan(process)
    except (DeviceError, timeouts.StepTimeout, reconnect.DeviceGone) as error:
        warn(f"plan_not_pulled: {one_line(error)}")


def stopped(device):
    try:
        device.force_stop()
    except DeviceLost as lost:
        warn(f"device_lost: the app could not be force-stopped; {str(lost).split(': ', 1)[-1]}")


def closed(process, hooks, waits):
    """Every hook's after_process, so one failing still leaves the others closed and the pulled data converted; the first error, else None."""
    failed = None
    for hook in reversed(hooks):
        try:
            waits.retried(lambda hook=hook: hook.after_process(process), f"{type(hook).__name__}.after_process")
        except Exception as error:
            if failed:
                warn(f"hook_failed: {type(hook).__name__}.after_process: {type(error).__name__}: {one_line(error)}")
            failed = failed or error
    return failed


def measure(device, plan, process, hooks):
    print(f"measure:   {plan.test_class} on the device" + ("" if device.stream else "; --stream shows each case"))
    plan.reconnect.retried(lambda: clear_outputs(device, plan.cleared), "the clearing of the device's outputs")
    for stale in (process.data, *plan.stale):
        stale.unlink(missing_ok=True)
    each_case(device, plan, process, hooks)


def each_case(device, plan, process, hooks):
    if process.redo:
        process.cases = paths.Measurement(process.into).order.read_text().split()
        print(f"measure:   {len(process.redo)} of {len(process.cases)} cases of a kept run launched again")
        again(device, plan, process, hooks, rejected.run_of(plan.unit, process.into, process.repetition), process.redo)
        return
    process.cases = plan.order(process.repetition, plan.reconnect.retried(
        lambda: case_isolation.planned(device, plan.test_class, plan.arguments, plan.plan_skips), "the case listing"))
    print(f"measure:   one process per case ({len(process.cases)} cases)")
    case_files.opened(process.into)
    case_files.ordered(process.into, process.cases)
    measured = []
    for number, case in enumerate(process.cases, 1):
        failure = launch.run_of_case(device, plan, process, case, hooks, case_files.path(process.into, case))
        print(f"case:      {number} of {len(process.cases)} {case} {verdict(failure)}")
        if failure:
            print(failure)
            process.failures.append(failure)
        else:
            measured.append(case)
            # rewritten after every case, so an error that ends the session keeps every case measured before it
            case_files.merge(process.into, measured, process.data)
    if not measured and skips.every_case(process.failures):
        raise AllSkipped(f"{ALL_CASES_SKIPPED}: every case of {plan.test_class} is a coded preparation skip: {len(process.failures)} cases, "
                         f"listed in {paths.SKIPPED}")
    if not measured:
        raise DeviceError(f"{plan.test_class} failed on the device for every case:\n" + "\n".join(process.failures or ["no case planned"]))


def completed(device, plan, process, hooks):
    """check_run at the process's end, its plan pulled: a case without a file, or whose file now fails a rule, is launched once more in this
    process, before the next one starts."""
    run = rules.RunFolder(plan.unit, process.into, process.into, process.repetition, process.recorded + tuple(process.failures), sized=process.samples)
    findings = rules.failed(rules.check_run(run, plan.expectation))
    again(device, plan, process, hooks, run.run, {case: [f for f in findings if f.case == case] for case in rules.redone(findings)})


def again(device, plan, process, hooks, run, failed):
    """failed: {case: [Finding]}; each case's file moves to rejected/ and the case is launched again, then benchmarkData.json merged again."""
    for case, found in failed.items():
        attempt = 1 + sum(1 for entry in process.relaunched if entry["case"] == case)
        rejected.moved(plan.unit, rules.Result(run, case, case_files.path(process.into, case)), attempt, found)
        process.relaunched.append({"case": case, "attempt": attempt, "code": found[0].code})
        failure = launch.run_of_case(device, plan, process, case, hooks, case_files.path(process.into, case))
        print(f"case:      {case} launched again ({found[0].code}) {verdict(failure)}")
        if failure:
            print(failure)
            process.failures.append(failure)
    if failed:
        case_files.merge(process.into, [case for case in process.cases if case_files.path(process.into, case).is_file()], process.data)


def verdict(failure):
    return "ok" if not failure else "skipped" if skips.every_case([failure]) else "failed"

