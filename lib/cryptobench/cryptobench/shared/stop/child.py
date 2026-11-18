"""One way to stop a child started with start_new_session=True: SIGTERM to its group, its grace to end, then SIGKILL; and
stop_like_ctrl_c(), so a SIGTERM to this process stops it as Ctrl-C does."""
from __future__ import annotations

import os
import signal
import subprocess
import time

# a pipeline.py child's time to stop its device test and write its partial manifest
PIPELINE_GRACE_SECONDS = 120
POLL_SECONDS = 0.5
# no SIGHUP on Windows
STOP_SIGNALS = tuple(getattr(signal, name) for name in ("SIGTERM", "SIGHUP") if hasattr(signal, name))


def stop(process: subprocess.Popen, grace: float, poll: float = POLL_SECONDS) -> None:
    """Returns once the process has ended; a Ctrl-C during the grace kills the group at once."""
    _signal(process, signal.SIGTERM)
    deadline = time.monotonic() + grace
    try:
        while process.poll() is None and time.monotonic() < deadline:
            time.sleep(poll)
    except KeyboardInterrupt:
        pass
    if process.poll() is None:
        _signal(process, signal.SIGKILL)
    process.wait()


def _signal(process: subprocess.Popen, number: int) -> None:
    try:
        os.killpg(process.pid, number)
    except (ProcessLookupError, PermissionError):
        pass


def stop_like_ctrl_c() -> None:
    """kill and a closed terminal raise KeyboardInterrupt, so the process stops its children and records a partial run."""
    for number in STOP_SIGNALS:
        signal.signal(number, signal.default_int_handler)
