"""The one rules table a result is held against (decision 24): each row a code, its scope, severity and check. Findings are data; the launch
loop, the block end, the restart and the audit each decide what to do with them."""
import dataclasses, functools, json, pathlib, re, statistics

from cryptobench.shared import paths
from cryptobench.shared.document.document import read_yaml
from cryptobench.stages.measurement.session.blocks import run_files
from cryptobench.stages.measurement.validation.rejected import run_of

FAIL, NOTE = "fail", "note"
# PASS: a run row of the pass sized by its window (min_window, the energy pass) only
CASE, RUN, PASS = "case", "run", "pass"
# a problem line that names a case the run gave up on: no file is expected for it
GAVE_UP = ("case_failed: ", "case_skipped: ")
# androidx targets about 100 ms a sample; the collapsed samples seen on a Pixel 10 were under 0.1 ms
SHORT_SAMPLE_MS = 1.0
# androidx ends a warm-up at 8 s whether or not the timing has settled; it does not report which happened
WARMUP_NEAR_CAP_S = 6.0
# androidx prefixes a result with the error ids it suppressed: EMULATOR_measure[...], DEBUGGABLE_EMULATOR_measure[...]
SUPPRESSED_PREFIX = re.compile(r"^(?:[A-Z][A-Z0-9-]*_)+(?=measure\[)")


@dataclasses.dataclass(frozen=True)
class Finding:
    code: str
    scope: str
    run: str | None
    case: str | None
    detail: str
    severity: str

    def document(self):
        return dataclasses.asdict(self)


@dataclasses.dataclass(frozen=True)
class Result:
    """One attempt's pulled benchmarkData: run names its process folder, samples the count a relaunch asked for (None: the pass's)."""
    run: str
    case: str
    path: pathlib.Path
    samples: int | None = None

    @functools.cached_property
    def benchmarks(self):
        """Every benchmark of the file, or why there is none."""
        try:
            found = json.loads(self.path.read_text()).get("benchmarks") or []
            return found if found else "no benchmark"
        except (OSError, ValueError, AttributeError) as error:
            return f"nothing readable ({type(error).__name__})"


def _sample_ms(benchmark):
    return benchmark["repeatIterations"] * statistics.median(benchmark["metrics"]["timeNs"]["runs"]) / 1e6


def present(result, _expectation):
    return None if result.path.is_file() else "no benchmarkData.json after a passing run"


def names_its_case(result, _expectation):
    found = result.benchmarks
    named = found if isinstance(found, str) else found[0].get("name") if isinstance(found[0], dict) else None
    named = named if isinstance(named, str) else "nothing readable (no name)"
    if SUPPRESSED_PREFIX.sub("", named) != f"measure[{result.case}]":
        return f"the pulled benchmarkData.json names {named}, not measure[{result.case}]"
    return None


def sample_count(result, expectation):
    expected = expectation.samples_of(result.case, result.samples)
    runs = len(result.benchmarks[0]["metrics"]["timeNs"]["runs"])
    return None if expected is None or runs == expected else f"{runs} samples, {expected} expected"


def calibrated(result, _expectation):
    """Calls per sample collapsed: androidx's moving average, inflated by one stall, can fall to one call."""
    short = [b for b in result.benchmarks if _sample_ms(b) < SHORT_SAMPLE_MS]
    return "; ".join(f"{b['name']}: {b['repeatIterations']} calls per sample, {_sample_ms(b):.3f} ms a sample" for b in short) or None


def warmup_near_cap(result, _expectation):
    """A warm-up that probably ran out of time instead of settling."""
    lines = []
    for b in result.benchmarks:
        seconds = b["warmupIterations"] * statistics.median(b["metrics"]["timeNs"]["runs"]) / 1e9
        if seconds >= WARMUP_NEAR_CAP_S:
            lines.append(f"{b['name']}: about {seconds:.1f} s")
    return "; ".join(lines) or None


@dataclasses.dataclass(frozen=True)
class RunFolder:
    """One run as check_run reads it: problems its recorded lines, files its record's digests (None before a record exists)."""
    unit: pathlib.Path
    folder: pathlib.Path
    pass_folder: pathlib.Path
    repetition: int
    problems: tuple = ()
    files: dict | None = None
    # energy-samples.yaml's cases while the process still holds them; None reads the file
    sized: dict | None = None

    @property
    def run(self):
        return run_of(self.unit, self.folder, self.repetition)

    @functools.cached_property
    def order(self):
        """The cases the process launched; None for a host run, which keeps no per-case files."""
        order = paths.Measurement(self.folder).order
        return order.read_text().split() if order.is_file() else None

    def gave_up(self, case):
        return any(line.startswith(GAVE_UP) and f" {case}:" in line for line in self.problems)

    @property
    def expected(self):
        return [case for case in self.order or () if not self.gave_up(case)]

    @functools.cached_property
    def relaunched(self):
        """case -> the samples a short window's relaunch ran with, from energy-samples.yaml."""
        samples = paths.Measurement(self.folder).energy_samples
        cases = self.sized if self.sized is not None else (read_yaml(samples).get("cases") or {}) if samples.is_file() else {}
        return {case: entry["relaunched"]["samples"] for case, entry in cases.items() if isinstance(entry.get("relaunched"), dict)}

    def result(self, case):
        return Result(self.run, case, paths.Measurement(self.folder).case(case), self.relaunched.get(case))


def every_case_present(run, _expectation):
    return [(case, "no cases/<case>.json for a case the run launched and did not give up on")
            for case in run.expected if not paths.Measurement(run.folder).case(case).is_file()]


def no_extra_case(run, _expectation):
    cases = paths.Measurement(run.folder).cases
    launched = set(run.order or ())
    return [(path.stem, "a case file the run did not launch") for path in sorted(cases.glob("*.json")) if path.stem not in launched and not paths.litter(path)]


def files_match_record(run, _expectation):
    if run.files is None:
        return []
    now = run_files(run.folder, run.pass_folder)
    named = lambda path: path[len(paths.CASES) + 1:-len(".json")] if path.startswith(f"{paths.CASES}/") else None
    return [(named(path), f"{path}: {'missing' if path not in now else 'not recorded' if path not in run.files else 'its digest differs'}")
            for path in sorted(set(now) | set(run.files)) if now.get(path) != run.files.get(path)]


def window_kept_short(run, _expectation):
    """Decision 32: a window still short after its one relaunch is kept and flagged."""
    samples = paths.Measurement(run.folder).energy_samples
    cases = (read_yaml(samples).get("cases") or {}) if samples.is_file() else {}
    return [(case, f"{entry.get('windowSeconds')} s window kept below the minimum") for case, entry in cases.items() if entry.get("shortWindow")]


def window_covered(run, _expectation):
    energy = paths.Measurement(run.folder).energy
    cases = (json.loads(energy.read_text()).get("cases") or {}) if energy.is_file() else {}
    return [(case, "the timed phase reaches past the rail samples; no energy number") for case, entry in cases.items()
            if any("window_uncovered" in str(reason) for reason in entry.get("invalid") or [])]


@dataclasses.dataclass(frozen=True)
class Rule:
    code: str
    scope: str
    severity: str
    check: object


# in order; check_case stops at a case's first fail, so a later row reads a file the earlier ones accepted
RULES = (
    Rule("no_data", CASE, FAIL, present),
    Rule("result_mismatch", CASE, FAIL, names_its_case),
    Rule("miscalibrated", CASE, FAIL, calibrated),
    Rule("sample_count", CASE, FAIL, sample_count),
    Rule("warmup_near_cap", CASE, NOTE, warmup_near_cap),
    Rule("case_missing", RUN, FAIL, every_case_present),
    Rule("case_extra", RUN, NOTE, no_extra_case),
    Rule("files_differ", RUN, FAIL, files_match_record),
    Rule("short_window", PASS, NOTE, window_kept_short),
    Rule("window_uncovered", PASS, NOTE, window_covered),
)


def check_case(result, expectation):
    """The case rows' findings for one attempt, up to its first fail."""
    findings = []
    for rule in (row for row in RULES if row.scope == CASE):
        detail = rule.check(result, expectation)
        if detail:
            findings.append(Finding(rule.code, CASE, result.run, result.case, detail, rule.severity))
            if rule.severity == FAIL:
                break
    return findings


def failed(findings):
    return [finding for finding in findings if finding.severity == FAIL]


def check_run(run, expectation):
    """check_case for every case the run kept a file of, then the run rows; a host run, with no per-case files, only matches its record."""
    expectation = expectation.planned(paths.RunTree(run.unit).preparation.prepared)
    findings = []
    for case in (case for case in run.expected if paths.Measurement(run.folder).case(case).is_file()):
        findings += check_case(run.result(case), expectation)
    scopes = (RUN, PASS) if expectation.min_window is not None else (RUN,)
    for rule in (row for row in RULES if row.scope in scopes):
        findings += [Finding(rule.code, rule.scope, run.run, case, detail, rule.severity) for case, detail in rule.check(run, expectation)]
    return findings


def redone(findings):
    """The cases a fail names, each once, in order: what a run launches again."""
    return list(dict.fromkeys(finding.case for finding in failed(findings) if finding.case))
