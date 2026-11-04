"""Session hook: the energy source's window around a process, its traces, dry pass and joules."""
import contextlib

import energy_stage
from energy_session import DRY_CALLS
from session.measure import Hooks


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
