"""The took: line of a timed step."""
import time

from cryptobench.shared.log.stdout import TOOK, say


def elapsed(label, started):
    say(TOOK, f"{label} in {time.monotonic() - started:.1f}s")
