"""Session hook: the clock state around every process and case of a device session."""
from device import clocks
from session.measure import Hooks
from cryptobench import paths


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
        clocks.write(paths.Measurement(process.into).clocks, self.before, clocks.read(self.device), self.cases)
        if self.cases:
            hit = sum(1 for c in self.cases.values() if c["start"] or c["end"])
            print(f"clocks:    {hit} of {len(self.cases)} cases started or ended with a core capped below its maximum")
