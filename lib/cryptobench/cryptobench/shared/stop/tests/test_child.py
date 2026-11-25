"""stop(): SIGTERM to the child's group, its grace, then SIGKILL; a Ctrl-C during the grace kills at once."""
import subprocess, sys, time

from cryptobench.shared.stop import child
from cryptobench.shared.wait import until

HONOURS = "import time\ntime.sleep(60)\n"
DEAF = "import signal, sys, time\nsignal.signal(signal.SIGTERM, signal.SIG_IGN)\nprint('deaf', flush=True)\ntime.sleep(60)\n"


def started(script):
    process = subprocess.Popen([sys.executable, "-c", script], stdout=subprocess.PIPE, text=True, start_new_session=True)
    if script == DEAF:
        assert process.stdout.readline().strip() == "deaf"
    return process


def test_a_child_that_honours_sigterm_ends_with_it_before_the_grace():
    process, begun = started(HONOURS), time.monotonic()
    child.stop(process, 30, 0.05)
    assert process.returncode == -15 and time.monotonic() - begun < 10


def test_a_child_deaf_to_sigterm_is_killed_once_the_grace_has_passed():
    process, begun = started(DEAF), time.monotonic()
    child.stop(process, 0.5, 0.05)
    assert process.returncode == -9 and time.monotonic() - begun >= 0.5


def test_a_ctrl_c_during_the_grace_kills_at_once(monkeypatch):
    process, begun = started(DEAF), time.monotonic()

    class Interrupted(until.Clock):
        def sleep(self, _seconds):
            raise KeyboardInterrupt
    monkeypatch.setattr(until, "SYSTEM", Interrupted())
    child.stop(process, 60, 0.05)
    assert process.returncode == -9 and time.monotonic() - begun < 10


def test_a_child_already_gone_is_only_waited_for():
    process = subprocess.Popen([sys.executable, "-c", "pass"], start_new_session=True)
    process.wait()
    child.stop(process, 60, 0.05)
    assert process.returncode == 0
