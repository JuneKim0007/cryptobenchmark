"""What a run of one pass promised, from the run record's run block (effective.yaml's run: as measured), never the live config."""
import dataclasses

from cryptobench.shared.document.document import read_yaml


@dataclasses.dataclass(frozen=True)
class Expectation:
    """name: the pass, None the single pass; samples: the pass's per case, None leaves each case its own harness.iterations;
    min_window: the energy pass's minWindowSeconds."""
    name: str | None
    samples: int | None
    min_window: int | None = None
    # case -> harness.iterations of the run's prepared.yaml; read once the process pulled its plan
    iterations: dict = dataclasses.field(default_factory=dict)

    def samples_of(self, case, asked=None):
        """asked: the count a relaunch ran with; None when nothing says how many."""
        return asked or self.samples or self.iterations.get(case)

    def planned(self, prepared):
        """With the per-case iterations prepared.yaml holds, when the pass sets none and the file is there."""
        if self.samples is not None or not prepared.is_file():
            return self
        cases = read_yaml(prepared).get("cases") or []
        return dataclasses.replace(self, iterations={case["id"]: case["harness"]["iterations"] for case in cases
                                                     if isinstance(case.get("harness"), dict) and case["harness"].get("iterations")})


def of(run, name):
    """run: the run record's run block; name: the pass, None for the single pass."""
    if name is None:
        return Expectation(None, None)
    one = run["passes"][name]
    return Expectation(name, int(one["samples"]), one.get("minWindowSeconds"))
