"""Deadline: kills a child's whole process group once its seconds pass, or when its caller fails, so no call hangs
or outlives the run."""
from __future__ import annotations

import os
import signal
import subprocess
import threading


class Deadline:
    """The child must start with start_new_session=True: its grandchildren hold the output pipe open too."""

    def __init__(self, process: subprocess.Popen, seconds: int | None):
        """seconds: None waits forever, still killing the child when its caller fails."""
        self.process, self.seconds, self.expired = process, seconds, False
        self.timer = threading.Timer(seconds, self._expire) if seconds else None
        if self.timer:
            self.timer.daemon = True

    def _expire(self) -> None:
        self.expired = True
        self._kill()

    def _kill(self) -> None:
        try:
            os.killpg(self.process.pid, signal.SIGKILL)
        except (ProcessLookupError, PermissionError):
            pass

    def __enter__(self) -> "Deadline":
        if self.timer:
            self.timer.start()
        return self

    def __exit__(self, kind, *_) -> None:
        if self.timer:
            self.timer.cancel()
        # its own session no longer gets the terminal's Ctrl-C, so a caller that dies takes the child with it
        if kind is not None:
            self._kill()
