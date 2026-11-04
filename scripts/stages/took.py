"""The took: line of a timed step."""
import time


def elapsed(label, started):
    print(f"took:      {label} in {time.monotonic() - started:.1f}s")
