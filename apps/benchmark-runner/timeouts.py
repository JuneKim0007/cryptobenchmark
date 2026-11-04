"""Ceilings of the host's subprocess steps: a step past its ceiling is one coded error line, never a silent hang."""
import contextlib, subprocess, threading

# Seconds. A ceiling only catches a hang, so each is several times the longest real step (docs/run.md#timeouts).
SECONDS = {
    "adb": 10 * 60,
    "install": 60 * 60,
    "instrument": 12 * 60 * 60,
    "case": 60 * 60,
    "gradle": 4 * 60 * 60,
    "compile": 30 * 60,
    "energy": 2 * 60 * 60,
    "analysis": 30 * 60,
}


class StepTimeout(Exception):
    pass


def expired(step, command):
    shown = " ".join(map(str, command))
    return StepTimeout(f"timeout: {step} ran past {SECONDS[step]} s: {shown[:300]}")


def run(step, command, **options):
    try:
        return subprocess.run(command, timeout=SECONDS[step], **options)
    except subprocess.TimeoutExpired:
        raise expired(step, command) from None


@contextlib.contextmanager
def watched(step, process, command):
    """A streamed process: killed at its ceiling, which then raises once its output has ended."""
    fired = threading.Event()

    def kill():
        fired.set()
        process.kill()

    timer = threading.Timer(SECONDS[step], kill)
    timer.daemon = True
    timer.start()
    try:
        yield
    finally:
        timer.cancel()
    if fired.is_set():
        raise expired(step, command)
