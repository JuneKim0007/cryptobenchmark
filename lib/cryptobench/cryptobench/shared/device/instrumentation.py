"""One instrumentation step on the device: its outputs cleared, the test class run and judged by its pass rule, its files pulled; run() waits out
a lost transport and runs the whole step again, clears included."""
from __future__ import annotations

import contextlib
import dataclasses
import re
from pathlib import Path
from typing import Callable

from cryptobench.shared.device.adb import PASSED, DeviceError, instrumentation_report

BEFORE, AFTER = "before", "after"


class Failed(DeviceError):
    """The test class ran and did not pass; output is what it printed."""

    def __init__(self, test_class, output):
        super().__init__(f"{test_class} failed on the device:\n" + instrumentation_report(output))
        self.output = output


@dataclasses.dataclass(frozen=True)
class Instrumented:
    test_class: str
    # remote paths: rm -f, rm -rf
    cleared: tuple[str, ...] = ()
    cleared_dirs: tuple[str, ...] = ()
    clear_when: str = BEFORE
    # None: the caller judges the output
    passed: re.Pattern | None = PASSED
    # (remote, local) after a pass, in order
    pulled: tuple[tuple[str, Path], ...] = ()


def clear(device, row):
    for command, targets in (("rm -rf", row.cleared_dirs), ("rm -f", row.cleared)):
        if targets:
            device.shell(f"{command} {' '.join(targets)}")


def once(device, row, *arguments, step="instrument", during: Callable[[], contextlib.AbstractContextManager] = contextlib.nullcontext):
    """The step's output; Failed when it did not pass. during wraps only the instrument call (a trace session)."""
    if row.clear_when == BEFORE:
        clear(device, row)
    with during():
        output = device.instrument(row.test_class, *arguments, step=step)
    if row.clear_when == AFTER:
        clear(device, row)
    if row.passed and not row.passed.search(output):
        raise Failed(row.test_class, output)
    for remote, local in row.pulled:
        Path(local).parent.mkdir(parents=True, exist_ok=True)
        device.pull(remote, local)
    return output


def run(device, waits, row, *arguments, **options):
    return waits.retried(lambda: once(device, row, *arguments, **options), f"the {row.test_class} run")
