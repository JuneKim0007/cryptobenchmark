"""Deadline: stops a child's whole process group once its seconds pass, or when its caller fails, so no call hangs
or outlives the run; the child gets SIGTERM and its grace before SIGKILL (shared/stop/child.py)."""
from __future__ import annotations

import subprocess
import threading

from cryptobench.shared.stop import child


class Deadline:
    """The child must start with start_new_session=True: its grandchildren hold the output pipe open too."""

    def __init__(self, process: subprocess.Popen, seconds: int | None, grace: float):
        """seconds: None waits forever, still stopping the child when its caller fails."""
        self.process, self.seconds, self.grace, self.expired = process, seconds, grace, False
        self.timer = threading.Timer(seconds, self._expire) if seconds else None
        if self.timer:
            self.timer.daemon = True

    def _expire(self) -> None:
        self.expired = True
        child.stop(self.process, self.grace)

    def __enter__(self) -> "Deadline":
        if self.timer:
            self.timer.start()
        return self

    def __exit__(self, kind, *_) -> None:
        if self.timer:
            self.timer.cancel()
        # its own session no longer gets the terminal's Ctrl-C, so a caller that dies takes the child with it
        if kind is not None:
            child.stop(self.process, self.grace)
