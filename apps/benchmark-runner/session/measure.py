"""One measuring session on the device: processes over repetitions, a process per case or one for all, and hooks around the session,
each process and each case."""
import dataclasses, pathlib, re

import effective_view
from failure import one_line
from results import case_files
from session import calibration, case_isolation, dynamic_temperature, launch
from device.adb import PASSED, DeviceError
from cryptobench import paths

COUNTED = re.compile(r"^Tests run: (\d+),\s+Failures: (\d+)", re.M)


def in_plan_order(_repetition, cases):
    return list(cases)


@dataclasses.dataclass(frozen=True)
class Plan:
    test_class: str
    arguments: tuple
    order: object = in_plan_order
    timed: bool = True
    cleared: tuple = ()
    stale: tuple = ()
    pull_plan: object = lambda _process: None
    after_process: object = lambda _process: None
    gate: object = dynamic_temperature.Off()
    retries: int = 0


@dataclasses.dataclass
class Process:
    repetition: int
    into: pathlib.Path
    cases: list = dataclasses.field(default_factory=list)
    failures: list = dataclasses.field(default_factory=list)

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


def run_session(device, plan, repetitions, isolation, hooks, folder, problems):
    """folder(repetition) is the process's folder; a case that failed is one problem line, a process that measured none the run's failure."""
    for hook in hooks:
        hook.before_session()
    processes = [one_process(device, plan, Process(repetition, folder(repetition)), isolation, hooks, repetitions, problems)
                 for repetition in range(1, repetitions + 1)]
    for hook in reversed(hooks):
        hook.after_session(processes)
    return processes


def one_process(device, plan, process, isolation, hooks, repetitions, problems):
    process_line(process.repetition, repetitions)
    process.into.mkdir(parents=True, exist_ok=True)
    started = []
    try:
        # a hook that fails here may have opened part of its step, so it is abandoned with those before it
        for hook in hooks:
            started.append(hook)
            hook.before_process(process)
        if plan.timed:
            measure(device, plan, process, isolation, hooks)
            plan.pull_plan(process)
    except BaseException as error:
        # the interrupt kills adb, not the test it started on the device
        if isinstance(error, KeyboardInterrupt):
            device.force_stop()
        for hook in reversed(started):
            hook.abandon(process)
        raise
    problems += process.failures
    failed = closed(process, hooks)
    plan.after_process(process)
    if failed:
        raise failed
    return process


def closed(process, hooks):
    """Every hook's after_process, so one failing still leaves the others closed and the pulled data converted; the first error, else None."""
    failed = None
    for hook in reversed(hooks):
        try:
            hook.after_process(process)
        except Exception as error:
            if failed:
                print(f"warning: hook_failed: {type(hook).__name__}.after_process: {type(error).__name__}: {one_line(error)}")
            failed = failed or error
    return failed


def measure(device, plan, process, isolation, hooks):
    print(f"measure:   {plan.test_class} on the device" + ("" if device.stream else "; --stream shows each case"))
    device.clear_outputs(plan.cleared)
    for stale in (process.data, *plan.stale):
        stale.unlink(missing_ok=True)
    if isolation == effective_view.CASE_ISOLATION:
        each_case(device, plan, process, hooks)
    else:
        all_cases(device, plan, process)


def planned(device, plan):
    return case_isolation.listed(device.instrument(plan.test_class, *plan.arguments, "-e", "log", "true"))


def each_case(device, plan, process, hooks):
    process.cases = plan.order(process.repetition, planned(device, plan))
    print(f"measure:   one process per case ({len(process.cases)} cases, isolation: case)")
    case_files.cleared(process.into)
    measured = []
    for number, case in enumerate(process.cases, 1):
        failure = launch.run_of_case(device, plan, process, case, hooks, case_files.path(process.into, case))
        print(f"case:      {number} of {len(process.cases)} {case} {'failed' if failure else 'ok'}")
        if failure:
            print(failure)
            process.failures.append(failure)
        else:
            measured.append(case)
            # rewritten after every case, so an error that ends the session keeps every case measured before it
            case_files.merge(process.into, measured, process.data)
    if not measured:
        raise DeviceError(f"{plan.test_class} failed on the device for every case:\n" + "\n".join(process.failures or ["no case planned"]))


def all_cases(device, plan, process):
    print("measure:   one process for every case (isolation: run)")
    output = device.instrument(plan.test_class, *plan.arguments)
    if not PASSED.search(output):
        counted = COUNTED.search(output)
        if not counted or counted.group(1) == counted.group(2):
            raise DeviceError(f"{plan.test_class} failed on the device:\n" + device.report(output))
        print(f"warning: {plan.test_class}: " + device.report(output).replace("\n", "\nwarning: "))
    device.pull(device.data, process.data)
    # one process for every case: nothing to measure again without repeating them all
    process.failures.extend(f"case_failed: {line}" for line in calibration.short_samples(process.data))
