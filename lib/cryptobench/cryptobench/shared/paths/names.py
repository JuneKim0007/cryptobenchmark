"""The names of a results folder, in one place; CONTRACT holds those Kotlin writes or reads too."""
from .device_dirs import PLAN_DIRECTORY, SCOPE_KEYS

MANIFEST, DEVICE = "manifest.yaml", "device.yaml"
CONFIGURATION, DISCOVERY, PREPARATION, BENCHMARK, ANALYSIS, CHART, CHECK, INTEROP, SCOPED = (
    "configuration", "discovery", "preparation", "benchmark", "analysis", "chart", "check", "interop", "scoped")
EFFECTIVE, INVENTORY, CONFIG_REPORT, GUIDE, KNOWN_ANSWERS = "effective.yaml", "inventory.yaml", "report.yaml", "guide.yaml", "known-answers.yaml"
CAPTURE_PREFIX, TRIAL_PREFIX, REQUIREMENTS_PREFIX = "probe", "trial", "requirements"
CAPTURE_PATTERN, TRIAL_FORM, REQUIREMENTS_FORM = f"{CAPTURE_PREFIX}_*.yaml", f"{TRIAL_PREFIX}_{{}}.yaml", f"{REQUIREMENTS_PREFIX}_{{}}.yaml"
GLOBAL, CONFIG_FOLDER = "global.yaml", "config"
ALGORITHM_NAMES, ENGINE_OPERATIONS, SETUP_CATALOG = "algorithm-names.yaml", "engine-operations.yaml", "setup-catalog.yaml"
FACTS, ENERGY_CAPABILITY, ENERGY_PREFLIGHT = "facts.yaml", "energy.yaml", "energy-preflight"
PREPARED, SKIPPED = "prepared.yaml", "skipped.yaml"
BENCHMARK_JSON, BENCHMARK_DATA, CLOCKS, THERMAL, CPU_PINS = "benchmark.json", "benchmarkData.json", "clocks.yaml", "thermal.json", "cpu-pins.yaml"
ENERGY_JSON, TRACES, DRY_TRACE, ENERGY_DRY, MANAFA = "energy.json", "traces", "dry.pftrace", "energy-dry.yaml", "manafa"
CASES, PROCESS_FORM = "cases", "process-{}"
CHECK_RESULT = "check.yaml"
INTEROP_PLAN, INTEROP_RESULT = "interop_plan.yaml", "interop.yaml"
SCOPED_PLAN_NAME, SCOPED_INTEROP, SCOPED_PLAN_FAILED = "scoped-plan.yaml", "scoped-interop.yaml", "scoped-plan.failed.yaml"
RUN_COUNTS_MD = "run-counts.md"
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

# (file name, the Kotlin constant that holds it); names_check.py compares it with the :files module, paths_check.py bans these as literals
CONTRACT = {
    KNOWN_ANSWERS: "FileNames.KNOWN_ANSWERS", CHECK_RESULT: "FileNames.CHECK_RESULT", BENCHMARK_JSON: "FileNames.BENCHMARK_JSON",
    ENERGY_CAPABILITY: "FileNames.ENERGY_CAPABILITY", ENERGY_JSON: "FileNames.ENERGY_JSON", ENERGY_DRY: "FileNames.ENERGY_DRY",
    INVENTORY: "FileNames.INVENTORY", EFFECTIVE: "FileNames.EFFECTIVE", CONFIG_REPORT: "FileNames.CONFIG_REPORT", GUIDE: "FileNames.GUIDE",
    PREPARED: "FileNames.PREPARED", SKIPPED: "FileNames.SKIPPED", INTEROP_RESULT: "FileNames.INTEROP_RESULT", INTEROP_PLAN: "FileNames.INTEROP_PLAN",
    CPU_PINS: "FileNames.CPU_PINS", SCOPED_INTEROP: "FileNames.SCOPED_INTEROP", ALGORITHM_NAMES: "FileNames.ALGORITHM_NAMES",
    ENGINE_OPERATIONS: "FileNames.ENGINE_OPERATIONS", SETUP_CATALOG: "FileNames.SETUP_CATALOG",
}
# Shared too, but ordinary words or an authored name other tools also spell: compared with Kotlin, not banned as Python literals.
CONTRACT_PARTS = {
    GLOBAL: "FileNames.GLOBAL", CONFIG_FOLDER: "Folders.CONFIG", CONFIGURATION: "Folders.CONFIGURATION", PREPARATION: "Folders.PREPARATION",
    PLAN_DIRECTORY: "Folders.DEVICE_PLAN", SCOPE_KEYS: "Folders.SCOPE_KEYS",
    CAPTURE_PREFIX: "StampedName.PROBE", TRIAL_PREFIX: "StampedName.TRIAL", REQUIREMENTS_PREFIX: "StampedName.REQUIREMENTS",
}
