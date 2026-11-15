"""A warning line of a stage."""


def warn(line, problems=None):
    """A warning on the terminal and, when the run keeps a list, in its manifest."""
    print(f"warning: {line}")
    if problems is not None:
        problems.append(line)
