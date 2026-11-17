"""A warning line: on the terminal, in the run's problems when it keeps a list, and one log event carrying the line's code."""
from cryptobench.shared.errors.coded import code_in
from cryptobench.shared.log.emit import emit
from cryptobench.shared.log.event import LOG

STAGE, STEP = "runner", "warning"


def warn(line, problems=None):
    print(f"warning: {line}")
    if problems is not None:
        problems.append(line)
    emit(STAGE, STEP, LOG, outcome="warn", detail=line, data={"code": code_in(line)})
