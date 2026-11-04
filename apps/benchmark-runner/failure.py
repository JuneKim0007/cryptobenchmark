"""One way to stop with a readable message."""
import sys


def one_line(error):
    return " ".join(str(error).split())[:500]


def fail(message):
    print(f"error: {message}", file=sys.stderr)
    raise SystemExit(1)
