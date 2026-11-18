"""The one rules table a result is held against (decision 24): each row a code, its scope, severity and check. Findings are data; the launch
loop, the block end, the restart and the audit each decide what to do with them."""
import dataclasses, functools, json, pathlib, re, statistics

FAIL, NOTE = "fail", "note"
CASE = "case"
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
