"""run.passes.energy.minWindowSeconds: a case's energy window from its pulled file, its one relaunch when short (decision 32), sized once
per run so every process holds equal samples, and the process's energy-samples.yaml."""
import dataclasses, json, math

from cryptobench.shared.document.document import DocumentKind, read_yaml
from cryptobench.shared.document.dump import dump_yaml
from cryptobench.shared.document.write import write_text
from cryptobench.shared.log.warn import warn
from cryptobench.stages.measurement.validation.rules import asked_samples

ENERGY_SAMPLES_DOC = DocumentKind("energySamples", 1)
# a relaunch aims past the minimum, since repeatIterations is picked again per process
MARGIN = 1.5


def seconds(pulled):
    """repeatIterations x the sum of timeNs.runs: the timed window Jetpack spent on the case."""
    benchmark = json.loads(pulled.read_text())["benchmarks"][0]
    return benchmark["repeatIterations"] * sum(benchmark["metrics"]["timeNs"]["runs"]) / 1e9


@dataclasses.dataclass(frozen=True)
class MinWindow:
    minimum: int
    samples: int
    # samples -> the pass's instrumentation arguments with that count
    arguments: object
    # case -> the samples the first process that measured it kept; every later process launches it with that count
    decided: dict = dataclasses.field(default_factory=dict)

    def first(self, case):
        """The first launch's arguments and the samples it asks for."""
        asked = self.decided.get(case, self.samples)
        return self.arguments(asked), asked

    def sized(self, process, case, pulled, asked, relaunched):
        """The samples of the one relaunch a short window gets, else None; records the case in process.samples. asked: the samples the launch
        just judged ran with; relaunched: that launch was the relaunch."""
        window = seconds(pulled)
        if relaunched:
            process.samples[case]["relaunched"] = {"samples": asked, "windowSeconds": round(window, 3)}
            self.decided[case] = asked
            if window < self.minimum:
                process.samples[case]["shortWindow"] = True
                warn(f"short_window: {case}: {window:.2f} s with {asked} samples, below {self.minimum} s")
            return None
        process.samples[case] = {"samples": asked, "windowSeconds": round(window, 3)}
        if case in self.decided:
            if window < self.minimum:
                process.samples[case]["shortWindow"] = True
                warn(f"short_window: {case}: {window:.2f} s with {asked} samples, below {self.minimum} s; sized by an earlier process")
            return None
        if window >= self.minimum:
            self.decided[case] = asked
            return None
        more = math.ceil(asked * MARGIN * self.minimum / window) if window > 0 else asked * 2
        print(f"window:    {case}: {window:.2f} s below {self.minimum} s; launching again with {more} samples")
        return more

    def kept_short(self, process, case, failure):
        """The relaunch failed every retry: the first, short window stays the case's result, and its count the run's."""
        process.samples[case]["shortWindow"] = True
        entry = process.samples[case]
        self.decided[case] = entry["samples"]
        warn(f"short_window: {case}: {entry['windowSeconds']:.2f} s with {entry['samples']} samples kept, below {self.minimum} s; "
             f"its relaunch failed: {failure}")

    def seeded(self, path):
        """A kept process's energy-samples.yaml: its cases' counts decide this run's."""
        cases = (read_yaml(path).get("cases") or {}) if path.is_file() else {}
        for case, entry in cases.items():
            self.decided.setdefault(case, asked_samples(entry))

    def write(self, process, path):
        document = {"schemaVersion": ENERGY_SAMPLES_DOC.version, "minWindowSeconds": self.minimum, "cases": process.samples}
        return write_text(path, dump_yaml(document))
