"""One measuring session on the device, shared by the benchmark and the before/after run: processes over repetitions, a process per case or
one for all, and hooks around the session, each process and each case."""
import dataclasses, json, pathlib, re

import case_isolation, effective_view
from device import DeviceError

PASSED = re.compile(r"^OK \(\d+ tests?\)", re.M)
COUNTED = re.compile(r"^Tests run: (\d+),\s+Failures: (\d+)", re.M)


def in_plan_order(_repetition, cases):
    return list(cases)


def alternating(repetition, cases):
    """Pairs (before, after) as AB in odd repetitions, BA in even ones: never a fixed order, so linear drift does not land on one side."""
    pairs = [cases[i:i + 2] for i in range(0, len(cases), 2)]
    return [case for pair in pairs for case in (pair if repetition % 2 else pair[::-1])]


@dataclasses.dataclass(frozen=True)
class Plan:
    """cases None lists them on the device in each process; named passes them as one ordered filter when one process runs them all."""
    test_class: str
    arguments: tuple
    cases: tuple | None = None
    order: object = in_plan_order
    named: bool = False
    timed: bool = True
    cleared: tuple = ()
    stale: tuple = ()
    pull_plan: object = lambda _process: None
    after_process: object = lambda _process: None


@dataclasses.dataclass
class Process:
    repetition: int
    into: pathlib.Path
    cases: list = dataclasses.field(default_factory=list)
    failures: list = dataclasses.field(default_factory=list)

    @property
    def data(self):
        return self.into / "benchmarkData.json"


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
    if repetitions > 1:
        print(f"process:   {process.repetition} of {repetitions}")
    process.into.mkdir(parents=True, exist_ok=True)
    for hook in hooks:
        hook.before_process(process)
    try:
        if plan.timed:
            measure(device, plan, process, isolation, hooks)
            plan.pull_plan(process)
    except BaseException:
        for hook in reversed(hooks):
            hook.abandon(process)
        raise
    problems += process.failures
    for hook in reversed(hooks):
        hook.after_process(process)
    plan.after_process(process)
    return process


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
    if plan.cases is not None:
        return list(plan.cases)
    return case_isolation.listed(device.instrument(plan.test_class, *plan.arguments, "-e", "log", "true"))


def each_case(device, plan, process, hooks):
    process.cases = plan.order(process.repetition, planned(device, plan))
    print(f"measure:   one process per case ({len(process.cases)} cases, isolation: case)")
    documents = []
    for case in process.cases:
        for hook in hooks:
            hook.before_case(process, case)
        document, failure = case_isolation.measure_case(device, plan.test_class, plan.arguments, case, process.into / f".{case}.json")
        for hook in reversed(hooks):
            hook.after_case(process, case, failure)
        if document is not None:
            documents.append(document)
        if failure:
            print(failure)
            process.failures.append(failure)
    if not documents:
        raise DeviceError(f"{plan.test_class} failed on the device for every case:\n" + "\n".join(process.failures or ["no case planned"]))
    process.data.write_text(json.dumps(case_isolation.merged(documents), indent=1))


def all_cases(device, plan, process):
    print("measure:   one process for every case (isolation: run)")
    process.cases = plan.order(process.repetition, plan.cases) if plan.cases is not None else []
    named = ("-e", case_isolation.CASE_ARGUMENT, ",".join(process.cases)) if plan.named and process.cases else ()
    output = device.instrument(plan.test_class, *plan.arguments, *named)
    if not PASSED.search(output):
        counted = COUNTED.search(output)
        if not counted or counted.group(1) == counted.group(2):
            raise DeviceError(f"{plan.test_class} failed on the device:\n" + device.report(output))
        print(f"warning: {plan.test_class}: " + device.report(output).replace("\n", "\nwarning: "))
    device.pull(device.data, process.data)
