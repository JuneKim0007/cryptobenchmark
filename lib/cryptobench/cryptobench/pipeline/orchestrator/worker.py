"""Worker: one pipeline.py child for one target's suite, in its own process group with its transcript in the target log; perf-repair's
child pattern (child/deadline.py): a caller that fails or is stopped stops the child's whole group."""
from __future__ import annotations

import dataclasses
import os
import signal
import subprocess
from pathlib import Path

from cryptobench.shared.errors.coded import code_in
from cryptobench.shared.log.stdout import ERROR, RESULTS, last

SERIAL = "ANDROID_SERIAL"


@dataclasses.dataclass(frozen=True)
class Outcome:
    state: str
    # the worker's last coded line, None when it finished
    line: str | None
    results: str | None

    @property
    def code(self) -> str | None:
        return code_in(self.line) if self.line else None


# a host run refuses --suppress-errors, which this variable sets
DEVICE_ONLY = (SERIAL, "CRYPTOBENCH_SUPPRESS_ERRORS")


def environment(serial: str | None) -> dict[str, str]:
    """The orchestrator's environment with ANDROID_SERIAL set to the target's serial; on the host without the device-only variables."""
    if serial:
        return {**{k: v for k, v in os.environ.items() if k != SERIAL}, SERIAL: serial}
    return {k: v for k, v in os.environ.items() if k not in DEVICE_ONLY}


class Worker:

    def __init__(self, command: list[str], serial: str | None, log: Path):
        self.command, self.serial, self.log = command, serial, log
        self.process: subprocess.Popen | None = None
        self.stopped = False

    def start(self) -> None:
        self.log.parent.mkdir(parents=True, exist_ok=True)
        with self.log.open("a") as out:
            self.process = subprocess.Popen(self.command, stdout=out, stderr=subprocess.STDOUT, stdin=subprocess.DEVNULL,
                                            env=environment(self.serial), start_new_session=True)

    def poll(self) -> int | None:
        return self.process.poll()

    def last_line(self) -> str:
        lines = [line for line in self.transcript() if line.strip()]
        return lines[-1] if lines else ""

    def transcript(self) -> list[str]:
        return self.log.read_text(errors="replace").splitlines() if self.log.is_file() else []

    def stop(self) -> None:
        """SIGTERM to the group: pipeline.py stops as on Ctrl-C and writes its partial manifest."""
        self.stopped = True
        try:
            os.killpg(self.process.pid, signal.SIGTERM)
        except (ProcessLookupError, PermissionError):
            pass

    def kill(self) -> None:
        try:
            os.killpg(self.process.pid, signal.SIGKILL)
        except (ProcessLookupError, PermissionError):
            pass

    def outcome(self) -> Outcome:
        lines = self.transcript()
        error = last(ERROR, lines)
        code = self.process.returncode
        state = "stopped" if self.stopped else "finished" if code == 0 else "failed"
        line = error if error is not None else None if code == 0 else f"subprocess_failed: pipeline.py exited {code}"
        return Outcome(state, line if state != "finished" else None, last(RESULTS, lines))
