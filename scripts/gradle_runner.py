"""Runs one gradle tool and turns its failure into the few lines a person needs."""
import subprocess
import sys

import timeouts

from failure import fail, one_line
from repo import ROOT

PASSED_ON = ("warning:", "skipped:", "reused:", "iterations_not_applied:", "allocation_runs_changed:", "not_in_plan:", "no_metrics:",
             "not_converted:", "not_merged:", "energy_not_joined:")
NOISE = ("FAILURE:", "BUILD FAILED", "* Try:", "* Get more help", "* What went wrong", "> Process 'command", "Run with --", "* Exception is:")


def failure_message(output):
    """The tool's own error lines and what follows them, else the last few lines that are not gradle's boilerplate."""
    reported, following = [], False
    for line in output:
        if line.startswith(("error:", "skipped:", "warning:")):
            reported.append(line[len("error: "):] if line.startswith("error: ") else line)
            following = True
        elif following and line.startswith("  "):
            reported.append(line)
        else:
            following = False
    fallback = [line for line in output if line.strip() and not line.startswith(NOISE)]
    return "\n".join(reported or fallback[-5:])[:2000]


class ToolFailed(Exception):
    pass


def _command(wrapper, project, arguments, main_class):
    command = [str(wrapper), "-p", str(ROOT / "tools" / project), "run", "--no-daemon", "-q"]
    # Gradle refuses an empty --args
    if arguments:
        command.append(f"--args={arguments}")
    if main_class:
        command.append(f"-PmainClass={main_class}")
    return command


def output_of(project, arguments, main_class):
    """The tool's stdout lines; its failure is one ToolFailed line, for a caller that goes on or words it itself."""
    wrapper = ROOT / "tools/jca-contract/gradlew"
    result = timeouts.run("gradle", _command(wrapper, project, arguments, main_class), capture_output=True, text=True)
    if result.returncode != 0:
        raise ToolFailed(one_line(failure_message((result.stdout + result.stderr).splitlines())))
    return result.stdout.strip().splitlines()


def run(project, arguments, stacktrace, stream=False, main_class=None, notices=None):
    """notices, when given, collects every passed-on line, so a caller can record it."""
    wrapper = ROOT / "tools/jca-contract/gradlew"
    if not wrapper.is_file():
        fail(f"missing_file: {wrapper}")
    command = _command(wrapper, project, arguments, main_class)
    if stream:
        result = timeouts.run("gradle", command, stdout=subprocess.PIPE, text=True)
        if result.returncode != 0:
            fail(f"{project} failed; rerun without --stream for a filtered message")
        return result.stdout.strip().splitlines()
    result = timeouts.run("gradle", command, capture_output=True, text=True)
    output = (result.stdout + result.stderr).splitlines()
    if result.returncode != 0:
        if stacktrace:
            print("\n".join(output), file=sys.stderr)
        fail(failure_message(output))
    pass_on(output, notices)
    return result.stdout.strip().splitlines()


def pass_on(output, notices):
    passed = [line for line in output if line.startswith(PASSED_ON)]
    for line in passed:
        print(line)
    if notices is not None:
        notices.extend(passed)
