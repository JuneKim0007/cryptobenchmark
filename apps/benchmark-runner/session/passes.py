"""run.passes: one device session per metric group, what each pass asks the device and converts, and the merge per metric of their results."""
import dataclasses, time

import effective_view
import gradle_runner
from failure import fail
from session.measure import process_folder

PASS_ARGUMENT = "cryptobench.pass"        # PassArguments.PASS
SAMPLES_ARGUMENT = "cryptobench.samples"  # PassArguments.SAMPLES
TIMING, ENERGY, ALLOCATION = "timing", "energy", "allocation"   # MeasurePass.NAMES
# The metric key each pass gives the merged benchmark.json; the timing pass gives every other key.
OWNED = {ENERGY: "energyJ", ALLOCATION: "allocationCount"}


@dataclasses.dataclass(frozen=True)
class Pass:
    """name None is the single pass: every metric in one session, the case's own iterations, files where they always were."""
    name: str | None
    samples: int | None
    metrics: tuple

    @property
    def label(self):
        return f"{self.name} pass" if self.name else "measure"

    def arguments(self):
        return () if self.name is None else ("-e", PASS_ARGUMENT, self.name, "-e", SAMPLES_ARGUMENT, str(self.samples))

    def folder(self, root):
        return root if self.name is None else root / self.name

    def captures(self, captures):
        return captures if self.name in (None, ENERGY) else {"none"}

    def convert_flags(self):
        return "" if self.name is None else f" --metrics={','.join(self.metrics)} --samples={self.samples}"


def read(document, captures):
    """The run's passes in the order written; none configured is the single pass."""
    run = document.get("run") or {}
    metrics, configured = effective_view.metrics(document), run.get("passes") or {}
    if not configured:
        return [Pass(None, None, tuple(metrics))]
    if "dry" in captures:
        fail("not_supported: energy.capture dry with run.passes; the energy pass measures `measured` cases and its samples set the window")
    configured = without_idle_energy(configured, captures)

    def metrics_of(name):
        if name == ENERGY:
            return ("TIME",)
        if name == ALLOCATION:
            return ("TIME", "ALLOCATION")
        return tuple(m for m in metrics if not (m == "ALLOCATION" and ALLOCATION in configured))
    return [Pass(name, int(value["samples"]), metrics_of(name)) for name, value in configured.items()]


def without_idle_energy(configured, captures):
    if ENERGY not in configured or "measured" in captures:
        return configured
    print("warning: run.passes.energy: no case sets harness.energy.capture measured; the energy pass is skipped")
    return {name: value for name, value in configured.items() if name != ENERGY}


def duration(seconds):
    hours, rest = divmod(int(seconds), 3600)
    return (f"{hours}h " if hours else "") + f"{rest // 60}m {rest % 60:02d}s"


def run_all(chosen, repetitions, root, measure_one, options):
    """measure_one(pass, folder, written) runs one pass's session; returns the per-process files the manifest lists."""
    results = {}
    for one in chosen:
        started, into, written = time.monotonic(), one.folder(root), []
        measure_one(one, lambda repetition, into=into: process_folder(into, repetition, repetitions), written)
        if repetitions > 1 and written:
            merge_runs(into, written, options)
        results[one] = (into / "benchmark.json", written)
        print(f"pass:      {one.label}: {repetitions} process{'es' if repetitions > 1 else ''}, {duration(time.monotonic() - started)} on the device")
    if chosen[0].name is None:
        return results[chosen[0]][1]
    return merged(results, root, repetitions, options)


def merge_runs(into, written, options):
    gradle_runner.run(" ".join(map(str, [into, *written])), options.stacktrace, options.stream, main_class="MergeRunsKt")


def merged(results, root, repetitions, options):
    """root/benchmark.json from every pass, and with repetitions root/process-<n>/ from each pass's n-th process."""
    base = next(one for one in results if one.name == TIMING)
    owned = [(OWNED[one.name], results[one]) for one in results if one.name in OWNED]

    def merge(out, base_file, others):
        arguments = [str(out), str(base_file)] + [f"{key}={path}" for key, path in others]
        gradle_runner.run(" ".join(arguments), options.stacktrace, options.stream, main_class="MergePassesKt")
        return out / "benchmark.json"
    merge(root, results[base][0], [(key, files[0]) for key, files in owned])
    if repetitions == 1:
        return []
    return [merge(process_folder(root, n + 1, repetitions), process, [(key, files[1][n]) for key, files in owned if n < len(files[1])])
            for n, process in enumerate(results[base][1])]
