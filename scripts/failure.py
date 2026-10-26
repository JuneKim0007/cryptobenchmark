"""One way to stop with a readable message."""
import sys


def fail(message):
    print(f"error: {message}", file=sys.stderr)
    raise SystemExit(1)
