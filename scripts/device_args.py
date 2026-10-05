"""Launch arguments a device run needs for the metrics the plan asks for.

    device_args.py [effective.yaml]       one `-Pandroid.testInstrumentationRunnerArguments.<name>=<value>` per line

Iterations, warm-up and profiling reach androidx per case, through MicrobenchmarkConfig inside the app. What
cannot be set per case is a launch argument: CPU events, because androidx keeps that capture class internal.
TIME and ALLOCATION need nothing; androidx always measures both.
"""
import pathlib
import sys

import effective_view
from failure import fail

ROOT = pathlib.Path(__file__).resolve().parent.parent
PREFIX = "-Pandroid.testInstrumentationRunnerArguments."


def arguments(document):
    metrics = (document.get("run") or {}).get("metrics") or ["TIME"]
    args = {}
    if "CPU_EVENTS" in metrics:
        args["androidx.benchmark.cpuEventCounter.enable"] = "true"     # androidx's own default event list applies
    return args


def main():
    effective = pathlib.Path(sys.argv[1] if len(sys.argv) > 1 else ROOT / "results/configuration/effective.yaml")
    if not effective.is_file():
        fail(f"missing_file: {effective}")
    for name, value in arguments(effective_view.read(effective)["document"]).items():
        print(f"{PREFIX}{name}={value}")


if __name__ == "__main__":
    main()
