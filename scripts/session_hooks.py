"""Hooks every device session can use: the clock state around a process, and the energy source's window, traces, dry pass and joules."""
import contextlib

import clocks, energy_stage
from clocks import CLOCKS
from energy_session import DRY_CALLS
from measure_session import Hooks


class Clocks(Hooks):
    """Per case, the cores capped below their hardware maximum at its start and end; one sysfs read each, no event stream."""

    def __init__(self, device):
        self.device, self.before, self.case_start, self.cases = device, None, None, {}

    def before_process(self, _process):
        self.before, self.cases = clocks.read(self.device), {}

    def before_case(self, _process, _case):
        self.case_start = clocks.capped(clocks.read(self.device))

    def after_case(self, _process, case, _failure):
        self.cases[case] = {"start": self.case_start, "end": clocks.capped(clocks.read(self.device))}

    def after_process(self, process):
        clocks.write(process.into / CLOCKS, self.before, clocks.read(self.device), self.cases)
        if self.cases:
            hit = sum(1 for c in self.cases.values() if c["start"] or c["end"])
            print(f"clocks:    {hit} of {len(self.cases)} cases started or ended with a core capped below its maximum")


class EnergyCapture(Hooks):
    """The window spans the device run; a failed energy step costs that process its energy, never its timing."""

    def __init__(self, source, session, captures, discovery, preparation, problems, dry_pass, timed=True):
        self.source, self.session, self.captures = source, session, captures
        self.discovery, self.preparation, self.problems = discovery, preparation, problems
        self.dry_pass, self.timed, self.stack = dry_pass, timed, None

    def before_process(self, process):
        (process.into / "energy.json").unlink(missing_ok=True)
        for stale in (process.into / "traces").glob("*.perfetto-trace"):
            stale.unlink()
        self.stack = contextlib.ExitStack()
        self.stack.enter_context(self.source.window(process.into))

    def abandon(self, _process):
        self.stack.close()

    def after_case(self, process, case, _failure):
        """A case's own process may remove the earlier cases' traces on the device, so each case's trace is pulled at once."""
        if "measured" in self.captures and self.timed:
            expected = process.cases.index(case) + 1
            pulled = []
            energy_stage.guarded(self.problems, lambda: pulled.append(self.session.pull_traces(process.into / "traces", fresh=False)))
            count = pulled[0] if pulled else 0
            print(f"traces:    {case}: {count} pulled" + ("" if count >= expected else f", {expected} expected"))

    def after_process(self, process):
        with self.stack:
            if "measured" in self.captures and self.timed:
                energy_stage.guarded(self.problems, lambda: print(f"traces:    {self.session.pull_traces(process.into / 'traces', fresh=False)} pulled"))
            if "dry" in self.captures:
                self.dry_pass(process.into, guarded=self.timed)
        energy_stage.guarded(self.problems, lambda: self.source.joules(self.captures, self.discovery / "energy.yaml", self.preparation,
                                                                       process.data, process.into / "traces", process.into / DRY_CALLS,
                                                                       process.into / "energy.json"))
