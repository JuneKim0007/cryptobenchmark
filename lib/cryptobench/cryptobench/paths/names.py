"""The names of a results folder, in one place; CONTRACT holds those Kotlin writes or reads too."""

MANIFEST, DEVICE = "manifest.yaml", "device.yaml"
CONFIGURATION, DISCOVERY, PREPARATION, BENCHMARK, ANALYSIS, CHART, CHECK, INTEROP, SCOPED = (
    "configuration", "discovery", "preparation", "benchmark", "analysis", "chart", "check", "interop", "scoped")
EFFECTIVE, INVENTORY, CONFIG_REPORT, GUIDE, KNOWN_ANSWERS = "effective.yaml", "inventory.yaml", "report.yaml", "guide.yaml", "known-answers.yaml"
CAPTURE_PATTERN, TRIAL_FORM, REQUIREMENTS_FORM = "probe_*.yaml", "trial_{}.yaml", "requirements_{}.yaml"
FACTS, ENERGY_CAPABILITY, ENERGY_PREFLIGHT = "facts.yaml", "energy.yaml", "energy-preflight"
PREPARED, SKIPPED = "prepared.yaml", "skipped.yaml"
BENCHMARK_JSON, BENCHMARK_DATA, CLOCKS, THERMAL, CPU_PINS = "benchmark.json", "benchmarkData.json", "clocks.yaml", "thermal.json", "cpu-pins.yaml"
ENERGY_JSON, TRACES, DRY_TRACE, ENERGY_DRY, MANAFA = "energy.json", "traces", "dry.pftrace", "energy-dry.yaml", "manafa"
CASES, PROCESS_FORM = "cases", "process-{}"
CHECK_RESULT = "check.yaml"
INTEROP_PLAN, INTEROP_RESULT = "interop_plan.yaml", "interop.yaml"
SCOPED_PLAN_NAME, SCOPED_INTEROP, SCOPED_PLAN_FAILED = "scoped-plan.yaml", "scoped-interop.yaml", "scoped-plan.failed.yaml"
SUMMARY_MD, THROUGHPUT_CHART, LATENCY_CHART, STABILITY_CHART = "summary.md", "throughput.png", "latency.png", "stability.png"
CHART_DATA = "chart-data.json"

ROWS, MEASUREMENTS, RUN_LOG, SITES, PRIMITIVES = "rows.json", "measurements.json", "run_log.json", "sites.json", "primitives.tsv"
USED, USED_CONFIG, USED_TEST_SET = "used.json", "used-global.yaml", "used-testset.yaml"
BUNDLED_SUGGESTIONS, BUNDLED_CONFIG, METRICS_CONFIG = "bundled-suggestions.yaml", "bundled-global.yaml", "metrics-global.yaml"
TARGETS, APPS_INDEX, CHARTER, SUMMARY = "targets.yaml", "apps-index.tsv", "charter.json", "summary.json"
APP, SCOPES, UNITS, DOSSIERS = "app.json", "scopes.json", "units.json", "dossiers.json"
REPLACE, REPLACEMENTS, EDITS, HARNESS = "replace", "replacements.json", "edits.json", "harness.yaml"
UPGRADE, UPGRADES, CHECKED = "upgrade", "upgrades.json", "checked"
APP_REPORT, APP_REPORT_MD, FINISHED = "report.json", "report.md", "finished.json"
LOCK, RUNS, GROUPING, REVIEW = ".lock", "runs", "grouping", "review"
LOG, EVENTS, STATUS_LOG, BUG_LOG = "log", "log/events.jsonl", "log/status.log", "log/bug.log"
PRIMITIVES_MISSING, BENCHMARK_COVERAGE = "log/details/primitives_missing.yaml", "log/details/benchmark_coverage.yaml"
PIPELINE_LOGS, AI_LOGS = "log/pipeline", "log/ai"
SCOPED_PLAN = f"{SCOPED}/{SCOPED_PLAN_NAME}"

# (file name, the Kotlin constant that holds it); the later agreement test reads this
CONTRACT = {
    KNOWN_ANSWERS: "KnownAnswerFile.NAME", CHECK_RESULT: "CheckFile.NAME", BENCHMARK_JSON: "BenchmarkJson.NAME",
    ENERGY_CAPABILITY: "EnergyCapability.FILE", INVENTORY: "Configuration.INVENTORY", EFFECTIVE: "Configuration.EFFECTIVE",
    CONFIG_REPORT: "Configuration.REPORT", GUIDE: "Guide.NAME", PREPARED: "PreparedFile.NAME", SKIPPED: "SkipFile.NAME",
    INTEROP_RESULT: "InteropFile.NAME", INTEROP_PLAN: "InteropPlanFile.NAME", CPU_PINS: "CorePins.FILE",
    SCOPED_INTEROP: "ScopeInteropFile.FILE", ENERGY_DRY: "EnergyDryBenchmark.CALLS",
}
