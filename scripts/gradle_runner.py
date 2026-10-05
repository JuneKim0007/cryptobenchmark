"""Runs one gradle tool and turns its failure into the few lines a person needs."""
import pathlib
import subprocess
import sys

from failure import fail

ROOT = pathlib.Path(__file__).resolve().parent.parent
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


def run(project, arguments, stacktrace, stream=False, main_class=None):
    wrapper = ROOT / "tools/jca-contract/gradlew"
    if not wrapper.is_file():
        fail(f"missing_file: {wrapper}")
    command = [str(wrapper), "-p", str(ROOT / "tools" / project), "run", "--no-daemon", "-q", f"--args={arguments}"]
    if main_class:
        command.append(f"-PmainClass={main_class}")
    if stream:
        result = subprocess.run(command, stdout=subprocess.PIPE, text=True)
        if result.returncode != 0:
            fail(f"{project} failed; rerun without --stream for a filtered message")
        return result.stdout.strip().splitlines()
    result = subprocess.run(command, capture_output=True, text=True)
    output = (result.stdout + result.stderr).splitlines()
    if result.returncode != 0:
        if stacktrace:
            print("\n".join(output), file=sys.stderr)
        fail(failure_message(output))
    for line in output:
        if line.startswith(("warning:", "skipped:", "reused:")):
            print(line)
    return result.stdout.strip().splitlines()
