"""One way to stop with a readable message."""
import contextlib
import sys


def fail(message):
    print(f"error: {message}", file=sys.stderr)
    raise SystemExit(1)


@contextlib.contextmanager
def reported():
    """A CommandError as fail() prints it; CommandError is imported here because dependencies.py imports this file before it checks for cryptobench."""
    from cryptobench.shared.errors.failures import CommandError
    try:
        yield
    except CommandError as error:
        fail(str(error))

