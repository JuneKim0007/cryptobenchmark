"""run.passes.energy.minWindowSeconds: a case's energy window from its pulled file, its one relaunch when short (decision 32), and the
process's energy-samples.yaml."""
import dataclasses, json, math

from cryptobench.shared.document.document import DocumentKind
from cryptobench.shared.document.dump import dump_yaml
from cryptobench.shared.document.write import write_text
from cryptobench.shared.log.warn import warn

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

    def sized(self, process, case, pulled, relaunched):
        """The samples of the one relaunch a short window gets, else None; records the case in process.samples. relaunched: the samples the
        launch just judged ran with, None for the first."""
        window = seconds(pulled)
        if relaunched is None:
            process.samples[case] = {"samples": self.samples, "windowSeconds": round(window, 3)}
            if window >= self.minimum:
                return None
            more = math.ceil(self.samples * MARGIN * self.minimum / window) if window > 0 else self.samples * 2
            print(f"window:    {case}: {window:.2f} s below {self.minimum} s; launching again with {more} samples")
            return more
        process.samples[case]["relaunched"] = {"samples": relaunched, "windowSeconds": round(window, 3)}
        if window < self.minimum:
            process.samples[case]["shortWindow"] = True
            warn(f"short_window: {case}: {window:.2f} s with {relaunched} samples, below {self.minimum} s")
        return None

    def kept_short(self, process, case, failure):
        """The relaunch failed every retry: the first, short window stays the case's result."""
        process.samples[case]["shortWindow"] = True
        entry = process.samples[case]
        warn(f"short_window: {case}: {entry['windowSeconds']:.2f} s with {entry['samples']} samples kept, below {self.minimum} s; "
             f"its relaunch failed: {failure}")

    def write(self, process, path):
        document = {"schemaVersion": ENERGY_SAMPLES_DOC.version, "minWindowSeconds": self.minimum, "cases": process.samples}
        return write_text(path, dump_yaml(document))
