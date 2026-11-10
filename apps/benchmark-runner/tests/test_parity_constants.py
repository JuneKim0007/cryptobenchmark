"""Values the runner and lib/cryptobench hold that a Kotlin source holds too, paired by comment only: each read from the Kotlin text
by a narrow pattern that must match once, so a rename on either side fails here. perf-repair's mirrors are in its own test."""
import ast
import pathlib
import re

import bundled
from analysis import chart_input
from session import case_isolation, passes, thermal_hook, variant_order
from scope import wrapper
from stages import check
from device import capture
from cryptobench.catalogue import guide_items, names, vectors
from cryptobench.paths import device_dirs
import energy, preflight
from rails import trace

ROOT = pathlib.Path(__file__).resolve().parents[3]
RUNNER = ROOT / "apps/benchmark-runner"
KM = ROOT / "apps/benchmark/modules"
AT = KM / "android/src/androidTest/kotlin/io/github/junekim0007/cryptobench"
CLI = ROOT / "apps/benchmark/cli/src/main/kotlin"


def kotlin(path, pattern):
    """The one match of pattern in a Kotlin file: its first group."""
    found = re.findall(pattern, (KM / path if not str(path).startswith("/") else path).read_text())
    assert len(found) == 1, f"{path}: {pattern} matched {len(found)} times"
    return found[0]


def const(path, name):
    return kotlin(path, rf'\bconst val {name} = "([^"]*)"')


def number(path, name):
    return int(kotlin(path, rf'\bconst val {name} = (\d+)\b'))


def runner_strings():
    """Every string constant in the runner's production Python."""
    found = set()
    for path in RUNNER.rglob("*.py"):
        if {"tests", "__pycache__"}.isdisjoint(path.relative_to(RUNNER).parts):
            found |= {n.value for n in ast.walk(ast.parse(path.read_text())) if isinstance(n, ast.Constant) and isinstance(n.value, str)}
    return found


def test_pass_arguments_and_pass_names():
    assert passes.PASS_ARGUMENT == const(AT / "PassArguments.kt", "PASS")
    assert passes.SAMPLES_ARGUMENT == const(AT / "PassArguments.kt", "SAMPLES")
    measure_pass = "config/src/main/kotlin/global/dto/MeasurePass.kt"
    assert (passes.TIMING, passes.ENERGY, passes.ALLOCATION) == tuple(const(measure_pass, n) for n in ("TIMING", "ENERGY", "ALLOCATION"))
    assert kotlin(measure_pass, r"val NAMES: List<String> = listOf\(([^)]*)\)") == "TIMING, ENERGY, ALLOCATION"
    # the androidTest copy, which cannot see :config
    assert (passes.ENERGY, passes.ALLOCATION) == (const(AT / "PassArguments.kt", "ENERGY"), const(AT / "PassArguments.kt", "ALLOCATION"))


def test_the_metrics_each_pass_measures():
    document = {"run": {"metrics": ["TIME", "ALLOCATION"], "passes": {"timing": {"samples": 3}, "energy": {"samples": 2}, "allocation": {"samples": 4}}}}
    python = {p.name: p.metrics for p in passes.read(document, {"measured"})}
    rules = dict(re.findall(r"^\s*(ENERGY|ALLOCATION|else) -> (.+?),?$", (AT / "PassArguments.kt").read_text(), re.M))
    assert rules["ENERGY"] == "setOf(Metric.TIME)" and python["energy"] == ("TIME",)
    assert rules["ALLOCATION"] == "setOf(Metric.TIME, Metric.ALLOCATION)" and python["allocation"] == ("TIME", "ALLOCATION")
    # current behaviour: the device keeps a case's own metrics in the timing pass; Python converts it without ALLOCATION
    assert rules["else"] == "settings.metrics" and python["timing"] == ("TIME",)
    assert re.split(r",\s*", kotlin("settings/src/main/kotlin/Metric.kt", r"enum class Metric \{\s*(\w+,\s*\w+);")) == ["TIME", "ALLOCATION"]


def test_metric_keys_of_benchmark_json():
    samples = "benchmark/src/main/kotlin/report/MetricSamples.kt"
    assert passes.OWNED == {passes.ENERGY: const(samples, "ENERGY"), passes.ALLOCATION: const(samples, "ALLOCATIONS")}
    assert const(AT / "SampledAllocations.kt", "NAME") == const(samples, "SAMPLED_ALLOCATIONS")


def test_instrumentation_arguments():
    assert case_isolation.CASE_ARGUMENT == const(AT / "CaseFilter.kt", "ARGUMENT")
    assert check.DRY_RUN == ["-e", const(AT / "EndToEndCheck.kt", "DRY_RUN"), "true"]
    assert const(AT / "DeviceProbe.kt", "HOST_MILLIS") == "hostMillis" and '"DeviceProbe", "-e", "hostMillis"' in (RUNNER / "device/adb.py").read_text()
    assert bundled.KEY == const("environment/discovery/src/main/kotlin/bundled/BundledProviders.kt", "KEY")


def test_package_and_device_folders():
    assert device_dirs.PACKAGE == kotlin(KM / "android/build.gradle", r"namespace '([^']+)'")
    assert f"{wrapper.PACKAGE}.{wrapper.CATALOG}" == const(AT / "ScopeCatalog.kt", "GENERATED")
    # Build.VERSION_CODES.Q is API 29
    assert device_dirs.MEDIA_FROM_SDK == 29
    assert kotlin(AT / "DeviceDirectory.kt", r"SDK_INT >= Build\.VERSION_CODES\.(\w+)\)") == "Q"


def test_labels_both_sides_write():
    assert trace.MARKER_PREFIX == const("benchmark/src/main/kotlin/run/decorate/EnergyWindow.kt", "PREFIX")
    assert variant_order.VARIANTS == tuple(re.findall(r'\b[A-Z_]+\("(\w+)"\)', (KM / "preparation/src/main/kotlin/measurement/Variant.kt").read_text()))
    group = kotlin("preparation/src/main/kotlin/prepare/ChartGroup.kt", r'UNIDENTIFIED\((\d+), "([^"]+)"\)')
    assert chart_input.UNIDENTIFIED == (int(group[0]), group[1])


def test_the_case_listing_reads_the_measure_method_by_name():
    source = (AT / "CryptoBenchmark.kt").read_text()
    assert re.search(r"@Test\s+fun measure\(\)", source) and '@Parameterized.Parameters(name = "{0}")' in source
    assert case_isolation.listed("INSTRUMENTATION_STATUS: test=measure[Cipher_AES_ENCRYPT]\n") == ["Cipher_AES_ENCRYPT"]


def test_instrumentation_classes_the_runner_names_exist_with_tests():
    named = {"CryptoBenchmark", "DeviceProbe", "EndToEndCheck", "EnergyDryBenchmark", "InteropCheck", "ScopedInterop"}
    tested = {p.stem for p in AT.glob("*.kt") if "@Test" in p.read_text()}
    assert tested == named and named <= runner_strings()


def test_host_main_classes_the_runner_names_exist():
    called = set()
    for path in RUNNER.rglob("*.py"):
        if "tests" not in path.relative_to(RUNNER).parts:
            called |= set(re.findall(r'main_class="(\w+)Kt"', path.read_text()))
    assert called == {"Probe", "Configure", "RuntimeFields", "Bench", "Check", "Interop", "Convert", "MergeRuns", "MergePasses"}
    assert all(re.search(r"^fun main\(", (CLI / f"{name}.kt").read_text(), re.M) for name in called)
    # CheckConfigKt goes through output_of with its name in a variable; CheckDiffKt has no Python caller
    assert '"CheckConfigKt"' in (RUNNER / "stages/config_check.py").read_text()


def test_thermal_json_keys():
    case_document = "benchmark/src/main/kotlin/report/CaseDocument.kt"
    keys = set(kotlin(case_document, r"val THERMAL_KEYS = setOf\(([^)]*)\)").replace('"', "").replace(" ", "").split(","))
    reading = type("Reading", (), {"sensors": {"cpu0": 1.0}, "status": 0, "reason": "r", "source": "hal"})()
    record = thermal_hook.record(reading, reading)
    assert set(record) - {"note"} == keys and const(case_document, "NOTE") == "note" and const(case_document, "GATE") == "gate"


def test_schema_versions_across_the_boundary():
    pairs = [
        (capture.SCHEMA, number("environment/discovery/src/main/kotlin/contract/CapturedEnvironment.kt", "SCHEMA_VERSION")),
        (capture.SCHEMA, number("preparation/src/main/kotlin/device/CaptureFile.kt", "SUPPORTED_SCHEMA_VERSION")),
        (capture.SCHEMA, int(kotlin("config/src/main/kotlin/source/CaptureSource.kt", r"override val schemaVersion: Int = (\d+)"))),
        (guide_items.SCHEMA_VERSION, number("preparation/src/main/kotlin/guide/Guide.kt", "SUPPORTED_SCHEMA_VERSION")),
        (vectors.SCHEMA_VERSION, int(kotlin("benchmark/src/main/kotlin/verify/known/KnownAnswerFile.kt", r'DocumentFile\.read\(file, "known_answers", (\d+)\)'))),
        (energy.SCHEMA_VERSION, number("benchmark/src/main/kotlin/report/energy/EnergyWindows.kt", "SCHEMA_VERSION")),
        (preflight.capability({}, {}, 1, False)["schemaVersion"],
         int(kotlin("benchmark/src/main/kotlin/check/EnergyCapability.kt", r'document\["schemaVersion"\] == (\d+)'))),
        (names.SCHEMA_VERSION, number("config/src/main/kotlin/names/AlgorithmNames.kt", "SCHEMA_VERSION")),
        (int(re.search(r'"schemaVersion": (\d+)', (RUNNER / "device/facts.py").read_text()).group(1)), int(kotlin("settings/src/main/kotlin/Facts.kt", r'document\["schemaVersion"\] == (\d+)'))),
    ]
    assert [python for python, _ in pairs] == [k for _, k in pairs]
    # thermal.json carries a version Python writes and no Kotlin reader checks (JetpackResults.thermalOf)
    assert thermal_hook.SCHEMA_VERSION == 1 and "schemaVersion" not in kotlin(
        "benchmark/src/main/kotlin/report/jetpack/JetpackResults.kt", r"(fun thermalOf\(text: String\)[^\n]*\n[^\n]*)")
