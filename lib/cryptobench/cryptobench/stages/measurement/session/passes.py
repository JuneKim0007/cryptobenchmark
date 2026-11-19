"""run.passes: one device session per metric group, what each pass asks the device and converts, and the merge per metric of their results."""
import dataclasses, time

from cryptobench.shared.device import gradle_runner
from cryptobench.shared.settings import effective_view
from cryptobench.shared.errors.failures import CommandError
from cryptobench.stages.measurement.session.measure import process_folder
from cryptobench.shared import paths
from cryptobench.shared.log.warn import warn

PASS_ARGUMENT = "cryptobench.pass"        # PassArguments.PASS
SAMPLES_ARGUMENT = "cryptobench.samples"  # PassArguments.SAMPLES
TIMING, ENERGY, ALLOCATION = "timing", "energy", "allocation"   # MeasurePass.NAMES
FIXED, MIN_WINDOW = "fixed", "min_window"


@dataclasses.dataclass(frozen=True)
class Row:
    # None: the run's metrics less those another configured pass owns
    metrics: tuple | None
    keeps_capture: bool
    # False converts --uncleaned: energy's samples are not GC-cleaned
    cleaned: bool
    # the metric key this pass gives the merged benchmark.json; the timing pass gives every other key
    owned: str | None
    # fixed: the configured samples; min_window: relaunched once when the window is short (window.py)
    sizing: str


# None is the single pass: every metric in one session, the case's own iterations, files where they always were
PASS_ROWS = {
    None: Row(None, True, True, None, FIXED),
    TIMING: Row(None, False, True, None, FIXED),
    ENERGY: Row(("TIME",), True, False, "energyJ", MIN_WINDOW),
    ALLOCATION: Row(("TIME", "ALLOCATION"), False, True, "allocationCount", FIXED),
}
OWNED = {name: row.owned for name, row in PASS_ROWS.items() if row.owned}


@dataclasses.dataclass(frozen=True)
class Pass:
    """One pass's view: its row of PASS_ROWS with the samples, metrics and minimum window the run gives it, the gate scope it holds
    under and its case cool-down (its own when :config wrote one, else the run's)."""
    name: str | None
    samples: int | None
    metrics: tuple
    min_window: int | None = None
    gate: str = effective_view.RUN_GATE
    cooldown: int = 0

    @property
    def row(self):
        return PASS_ROWS[self.name]

    @property
    def label(self):
        return f"{self.name} pass" if self.name else "measure"

    def arguments(self, samples=None):
        """samples: a relaunch's own count, which replaces the pass's."""
        return () if self.name is None else ("-e", PASS_ARGUMENT, self.name, "-e", SAMPLES_ARGUMENT, str(samples or self.samples))

    def folder(self, root):
        return root if self.name is None else root / self.name

    def captures(self, captures):
        return captures if self.row.keeps_capture else {"none"}

    def convert_flags(self):
        if self.name is None:
            return ""
        # a sized pass's cases ran with their own samples (energy-samples.yaml), so ConvertKt is not told one count
        samples = f" --samples={self.samples}" if self.row.sizing == FIXED else ""
        return f" --metrics={','.join(self.metrics)}{samples}" + ("" if self.row.cleaned else " --uncleaned")


def pass_views(view, captures):
    """view: effective_view.RunView. The run's passes in the order written; none configured is the single pass."""
    metrics, configured = view.metrics, view.passes or {}
    cooldown = lambda name: effective_view.required(view.document, effective_view.scoped(view.document, name, "caseCooldownSeconds"))
    if not configured:
        if "measured" in captures:
            raise CommandError("not_supported: energy.capture measured without run.passes.energy; energy is always measured in its own pass")
        return [Pass(None, None, tuple(metrics), cooldown=cooldown(None))]
    if "dry" in captures:
        raise CommandError("not_supported: energy.capture dry with run.passes; the energy pass measures `measured` cases and its samples set the window")
    configured = without_idle_energy(configured, captures)
    owned = {metric for name in configured for metric in (PASS_ROWS[name].metrics or ()) if metric != "TIME"}

    def one(name, value):
        row = PASS_ROWS[name]
        window = effective_view.required(view.document, f"run.passes.{name}.minWindowSeconds") if row.sizing == MIN_WINDOW else None
        return Pass(name, int(value["samples"]), row.metrics or tuple(m for m in metrics if m not in owned), window,
                    effective_view.scoped(view.document, name, "thermalGate"), cooldown(name))
    return [one(name, value) for name, value in configured.items()]


def without_idle_energy(configured, captures):
    if ENERGY not in configured or "measured" in captures:
        return configured
    warn("run.passes.energy: no case sets harness.energy.capture measured; the energy pass is skipped")
    return {name: value for name, value in configured.items() if name != ENERGY}


def duration(seconds):
    hours, rest = divmod(int(seconds), 3600)
    return (f"{hours}h " if hours else "") + f"{rest // 60}m {rest % 60:02d}s"


def run_all(chosen, repetitions, root, measure_one, options, finish=None):
    """measure_one(pass, folder, written) runs one pass's session; finish(), after the last pass, returns the passes it converted again,
    merged again here; returns the per-process files the manifest lists."""
    results = {}
    for one in chosen:
        started, into, written = time.monotonic(), one.folder(root), []
        measure_one(one, lambda repetition, into=into: process_folder(into, repetition, repetitions), written)
        if repetitions > 1 and written:
            merge_runs(into, written, options)
        results[one] = (paths.Measurement(into).json, written)
        print(f"pass:      {one.label}: {repetitions} process{'es' if repetitions > 1 else ''}, {duration(time.monotonic() - started)} on the device")
    for one in finish() if finish else ():
        if repetitions > 1 and results[one][1]:
            merge_runs(one.folder(root), results[one][1], options)
    if chosen[0].name is None:
        return results[chosen[0]][1]
    return merged(results, root, repetitions, options)


def merge_runs(into, written, options):
    gradle_runner.run(" ".join(map(str, [into, *written])), options.stacktrace, options.stream, main_class="MergeRunsKt")


def merged(results, root, repetitions, options):
    """root/benchmark.json from every pass, and with repetitions root/process-<n>/ from each pass's n-th process."""
    base = next((one for one in results if one.name == TIMING), next(iter(results)))
    owned = [(OWNED[one.name], results[one]) for one in results if one.name in OWNED]

    def merge(out, base_file, others):
        arguments = [str(out), str(base_file)] + [f"{key}={path}" for key, path in others]
        gradle_runner.run(" ".join(arguments), options.stacktrace, options.stream, main_class="MergePassesKt")
        return paths.Measurement(out).json
    merge(root, results[base][0], [(key, files[0]) for key, files in owned])
    if repetitions == 1:
        return []
    return [merge(process_folder(root, n + 1, repetitions), process, [(key, files[1][n]) for key, files in owned if n < len(files[1])])
            for n, process in enumerate(results[base][1])]
