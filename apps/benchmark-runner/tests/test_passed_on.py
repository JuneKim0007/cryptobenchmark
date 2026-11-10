"""The coded stderr lines the host Kotlin mains print, against gradle_runner.PASSED_ON: today's split, the dropped ones named."""
import pathlib
import re

import gradle_runner

ROOT = pathlib.Path(__file__).resolve().parents[3]
CLI = ROOT / "apps/benchmark/cli/src/main/kotlin"
REPORT = ROOT / "apps/benchmark/modules/benchmark/src/main/kotlin"
# every main, plus the module files whose lines a main prints: Convert and the merges print dropped and notApplied; BenchKt's plan logs skips
PRINTED = sorted(CLI.glob("*.kt")) + [
    REPORT / "report/jetpack/JetpackResults.kt", REPORT / "report/jetpack/RunCountAudit.kt", REPORT / "report/Merge.kt",
    REPORT / "report/PassMerge.kt", REPORT / "check/RunnablePlan.kt"]
CODED = re.compile(r'(?:System\.err\.println\(|dropped \+= |findings \+= |-> System\.err\.println\()"([a-z_]+:)')

EMITTED = {"error:", "usage:", "warning:", "skipped:", "reused:", "energy_not_joined:", "not_in_plan:", "no_metrics:", "not_converted:",
           "iterations_not_applied:", "allocation_runs_changed:", "not_merged:", "runtime_differs:"}


def emitted():
    return {code for path in PRINTED for code in CODED.findall(path.read_text())}


def test_the_coded_lines_the_mains_print_are_today_s_set():
    assert emitted() == EMITTED


def test_current_behaviour_every_printed_code_is_passed_on_but_runtime_differs():
    # error: and usage: belong to a failure, never passed on; runtime_differs: (MergeRunsKt) is dropped from terminal and manifest (C14)
    assert set(gradle_runner.PASSED_ON) <= EMITTED
    assert EMITTED - set(gradle_runner.PASSED_ON) - {"error:", "usage:"} == {"runtime_differs:"}


def test_current_behaviour_a_runtime_mismatch_is_not_passed_on(capsys):
    notices = []
    gradle_runner.pass_on(["not_merged: a: process 2: x", "runtime_differs: model: process 1 m, process 2 n", "merged=1 processes=2"], notices)
    assert notices == ["not_merged: a: process 2: x"] and capsys.readouterr().out == "not_merged: a: process 2: x\n"


def test_current_behaviour_bench_progress_after_a_skip_joins_the_failure_message():
    output = ["prepared=1 skipped=1", "skipped: Cipher X: no_key", "  Cipher_AES: median 12 ns/op", "error: nothing_measured"]
    assert gradle_runner.failure_message(output) == "skipped: Cipher X: no_key\n  Cipher_AES: median 12 ns/op\nnothing_measured"
