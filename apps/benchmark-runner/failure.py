"""One way to stop with a readable message."""
import contextlib
import sys


def one_line(error):
    return " ".join(str(error).split())[:500]


def fail(message):
    print(f"error: {message}", file=sys.stderr)
    raise SystemExit(1)


@contextlib.contextmanager
def reported():
    """A Stop as fail() prints it; Stop is imported here because dependencies.py imports this file before it checks for cryptobench."""
    from cryptobench.shared.errors.failures import Stop
    try:
        yield
    except Stop as error:
        fail(str(error))


def warn(line, problems=None):
    """A warning on the terminal and, when the run keeps a list, in its manifest."""
    print(f"warning: {line}")
    if problems is not None:
        problems.append(line)
