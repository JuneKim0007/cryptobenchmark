"""Hooks every device session can use: the clock state around a process, and the energy source's window, traces, dry pass and joules."""
import contextlib

import clocks, energy_stage
from clocks import CLOCKS
from energy_session import DRY_CALLS
from measure_session import Hooks


class Clocks(Hooks):

    def __init__(self, device):
        self.device, self.before = device, None

    def before_process(self, _process):
        self.before = clocks.read(self.device)

    def after_process(self, process):
        clocks.write(process.into / CLOCKS, self.before, clocks.read(self.device))


class EnergyCapture(Hooks):
    """The window spans the device run; a failed energy step costs that process its energy, never its timing."""

    def __init__(self, source, session, captures, discovery, preparation, problems, dry_pass, timed=True):
        self.source, self.session, self.captures = source, session, captures
        self.discovery, self.preparation, self.problems = discovery, preparation, problems
        self.dry_pass, self.timed, self.stack = dry_pass, timed, None

    def before_process(self, process):
        (process.into / "energy.json").unlink(missing_ok=True)
        self.stack = contextlib.ExitStack()
        self.stack.enter_context(self.source.window(process.into))

    def abandon(self, _process):
        self.stack.close()

    def after_process(self, process):
        with self.stack:
            if "measured" in self.captures and self.timed:
                energy_stage.guarded(self.problems, lambda: print(f"traces:    {self.session.pull_traces(process.into / 'traces')} pulled"))
            if "dry" in self.captures:
                self.dry_pass(process.into, guarded=self.timed)
        energy_stage.guarded(self.problems, lambda: self.source.joules(self.captures, self.discovery / "energy.yaml", self.preparation,
                                                                       process.data, process.into / "traces", process.into / DRY_CALLS,
                                                                       process.into / "energy.json"))
