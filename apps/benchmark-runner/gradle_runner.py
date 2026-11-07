"""Runs one command of the benchmark's CLI build and turns its failure into the few lines a person needs."""
import re
import subprocess
import sys

import timeouts

from failure import fail, one_line
from repo import BENCHMARK

WRAPPER = BENCHMARK / "gradlew"
CLI = BENCHMARK / "cli"
PASSED_ON = ("warning:", "skipped:", "reused:", "iterations_not_applied:", "allocation_runs_changed:", "not_in_plan:", "no_metrics:",
             "not_converted:", "not_merged:", "energy_not_joined:")
# the wrapper prints these on stdout the first time it unpacks a distribution, before the tool runs
BOOTSTRAP = ("Downloading https://services.gradle.org/", "Set executable permissions for:", "Unzipping ", "Welcome to Gradle")
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


def _command(arguments, main_class, properties=()):
    command = [str(WRAPPER), "-p", str(CLI), "run", "--no-daemon", "-q", f"-PmainClass={main_class}", *properties]
    # Gradle refuses an empty --args
    if arguments:
        command.append(f"--args={arguments}")
    return command


def tool_lines(stdout):
    """The tool's own stdout lines: the wrapper's bootstrap lines and its download progress dots dropped."""
    return [l for l in stdout.strip().splitlines() if not l.startswith(BOOTSTRAP) and not re.fullmatch(r"[.\d%]+", l.strip())]


def output_of(arguments, main_class):
    """The tool's stdout lines; its failure is one ToolFailed line, for a caller that goes on or words it itself."""
    result = timeouts.run("gradle", _command(arguments, main_class), capture_output=True, text=True)
    if result.returncode != 0:
        raise ToolFailed(one_line(failure_message((result.stdout + result.stderr).splitlines())))
    return tool_lines(result.stdout)


def run(arguments, stacktrace, stream=False, *, main_class, notices=None, properties=()):
    """notices, when given, collects every passed-on line, so a caller can record it; properties are -P build properties."""
    if not WRAPPER.is_file():
        fail(f"missing_file: {WRAPPER}")
    command = _command(arguments, main_class, properties)
    if stream:
        result = timeouts.run("gradle", command, stdout=subprocess.PIPE, text=True)
        if result.returncode != 0:
            fail(f"{main_class} failed; rerun without --stream for a filtered message")
        return tool_lines(result.stdout)
    result = timeouts.run("gradle", command, capture_output=True, text=True)
    output = (result.stdout + result.stderr).splitlines()
    if result.returncode != 0:
        if stacktrace:
            print("\n".join(output), file=sys.stderr)
        fail(failure_message(output))
    pass_on(output, notices)
    return tool_lines(result.stdout)


def pass_on(output, notices):
    passed = [line for line in output if line.startswith(PASSED_ON)]
    for line in passed:
        print(line)
    if notices is not None:
        notices.extend(passed)
