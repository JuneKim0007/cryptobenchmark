"""perf-repair's copies of benchmark Kotlin values: pass and metric names, what each harness measures, the case-id rule. Each Kotlin value
is read by a narrow pattern that must match once."""
import re
from pathlib import Path

from perfrepair.catalog import identity
from perfrepair.device import measures
from perfrepair.dto import metrics

KM = Path(__file__).resolve().parents[2] / "benchmark/modules"
AT = KM / "android/src/androidTest/kotlin/io/github/junekim0007/cryptobench"


def kotlin(path, pattern):
    found = re.findall(pattern, (KM / path).read_text())
    assert len(found) == 1, f"{path}: {pattern} matched {len(found)} times"
    return found[0]


def const(path, name):
    return kotlin(path, rf'\bconst val {name} = "([^"]*)"')


def test_metric_names_and_the_pass_that_measures_each():
    samples = "benchmark/src/main/kotlin/report/MetricSamples.kt"
    assert [m.name for m in metrics.METRICS] == [const(samples, n) for n in ("TIME", "ALLOCATIONS", "ENERGY")]
    passes = [const("config/src/main/kotlin/global/dto/MeasurePass.kt", n) for n in ("TIMING", "ALLOCATION", "ENERGY")]
    assert [m.passName for m in metrics.METRICS] == passes
    assert measures.ALLOCATION_PASS == passes[1]


def test_run_metric_names_and_what_each_harness_measures():
    run = re.split(r",\s*", kotlin("settings/src/main/kotlin/Metric.kt", r"enum class Metric \{\s*(\w+,\s*\w+);"))
    assert (metrics.TIME.run, metrics.ALLOCATIONS.run) == tuple(run) == (measures.DEFAULT_METRICS[0], measures.ALLOCATION_RUN)
    assert kotlin("benchmark/src/main/kotlin/run/HostHarness.kt", r"val METRICS: Set<Metric> = (.+)") == "setOf(Metric.TIME)"
    assert measures.HOST.metrics == ("TIME",)
    assert kotlin(AT.relative_to(KM) / "JetpackConfig.kt", r"val METRICS: Set<Metric> = (.+)") == "Metric.entries.toSet()"
    assert measures.DEVICE.metrics == tuple(run)


def test_the_case_id_rule():
    name = "preparation/src/main/kotlin/measurement/CaseName.kt"
    assert identity.UNSAFE.pattern == kotlin(name, r'val UNSAFE = Regex\("([^"]+)"\)')
    assert '"p" + java.lang.Long.toHexString(checksum.value).padStart(8, \'0\')' in (KM / name).read_text()
    assert identity.PARAMETERS_TAG == r"(?:_p[0-9a-f]{8})?"
    assert kotlin(name, r"\.joinToString\(\"(.)\"\)") == "_"
