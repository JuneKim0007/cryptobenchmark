"""A caller that fails inside Deadline: a child writing past the pipe buffer while it stops still ends within its grace, not at SIGKILL."""
import subprocess, sys, time

import pytest

from perfrepair.child.deadline import Deadline

LOUD_ON_TERM = """import signal, sys, time
def stopped(*_):
    sys.stdout.write("x" * 1_000_000); sys.stdout.flush(); sys.exit(130)
signal.signal(signal.SIGTERM, stopped)
print("ready", flush=True)
time.sleep(60)
"""


def test_a_child_loud_while_stopping_ends_before_its_grace_when_the_caller_fails():
    started = time.monotonic()
    with pytest.raises(RuntimeError):
        with subprocess.Popen([sys.executable, "-c", LOUD_ON_TERM], stdout=subprocess.PIPE, start_new_session=True) as process, \
                Deadline(process, None, 30):
            process.stdout.readline()
            raise RuntimeError("caller failed")
    assert process.returncode == 130 and time.monotonic() - started < 10
