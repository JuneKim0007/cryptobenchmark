"""Every stop, warn and skip code once: its default action, the actions `stops.<code>` may choose (none: fixed), exit
code and next step."""
from __future__ import annotations

from dataclasses import dataclass

STOP, WARN, SKIP = "stop", "warn", "skip"
ACTIONS = (STOP, WARN, SKIP)
MIXES = "continuing would mix runs or devices"
NOTHING = "nothing is left to run"
UNUSABLE = "the input is unusable"
NOTICE = "a notice; nothing to choose"
# the guide's step names: a step's coded failure is `<step>_failed`, the inner code kept beside it
GUIDE_STEPS = ("prerequisites", "targets", "grouping", "interop", "detect", "app", "dossier", "replace", "edit", "harness", "device", "report",
               "summary")


@dataclass(frozen=True)
class Code:
    code: str
    action: str
    next: str
    allowed: tuple[str, ...] = ()
    # every code exits 1 today; argparse refuses its own errors with 2 before any code is reached
    exit: int = 1
    why: str = UNUSABLE

    @property
    def fixed(self) -> bool:
        return not self.allowed


def _fixed(code: str, next_step: str, why: str = UNUSABLE, action: str = STOP) -> Code:
    return Code(code, action, next_step, (), 1, why)


def _choice(code: str, action: str, next_step: str, allowed: tuple[str, ...]) -> Code:
    return Code(code, action, next_step, allowed, 1, "")


RERUN_INBOUND = "rerun the inbound stage (or the guide's device stage)"
RERUN_GROUPING = "rerun grouping build, assign and report"
FIX_CATALOG = "fix the catalog file the message names"
FIX_PROMPTS = "fix the prompts folder or prompts.yaml the message names"
FIX_SETTINGS = "fix the value in perfrepair.yaml, the environment or the flag the message names"
PICK_DEVICE = "pass --device-results or set device.id"
STEP_LINES = "read the lines the step printed above; fix and rerun the guide"

CODES_LIST: tuple[Code, ...] = (
    # overridable through stops.<code>
    _choice("bundled_missing", WARN, "add the providers to providers.bundled in global.yaml, or set device.bundled.fromApps",
            (WARN, STOP)),
    _choice("not_on_device", WARN, "add it to providers.bundled in global.yaml and rerun the device stage", (WARN, STOP)),
    _choice("perf_mode_unmeasured", STOP, "measure on a device (guide --device), or drop the metric from apps.perfMode",
            (STOP, WARN)),
    _choice("perf_mode_maybe_unmeasured", WARN, "set run.harness.energy.capture: measured, or rely on the test set",
            (WARN, STOP)),
    _choice("energy_invalid", WARN, "the case has no energy number; rerun it with a longer window or more operations",
            (WARN, STOP)),
    _choice("energy_unreadable", WARN, "check the energy.json files the manifest lists", (WARN, STOP)),
    _choice("thermal_mismatch", WARN, "the sides of a pair started at different temperatures; rerun the pair, or read its ratio with care", (WARN, STOP)),
    _choice("category_mismatch", WARN, "the before/after disagrees with its category's estimate; check the scope's "
            "pattern against its function, or read its ratio with care", (WARN, STOP)),
    _choice("thermal_throttled_at_end", WARN, "the case ended throttled; let the phone cool, or read its numbers with care", (WARN, STOP)),
    _choice("no_required_metric", SKIP, "the case has no required metric runs; check the benchmark transcript",
            (SKIP, STOP)),
    _choice("invariant_undecided", WARN, "the source does not decide a rule; run python3 -m perfrepair.validation.invariants "
            "on the device folder and check each undecided finding by hand", (WARN, STOP)),
    _fixed("run_metrics_overridden", "remove run.metrics from the run config; apps.perfMode decides what is measured", NOTICE, WARN),
    _fixed("missing_dependency", "pip install -r requirements.txt"),
    # fixed: continuing would mix runs or devices
    _fixed("screening_catalog_mismatch", "rerun grouping build, or set device.screening.catalog to the catalog screen.json names",
           MIXES),
    _fixed("charter_mismatch", "move the outbox aside or restore the prompts it was made with", MIXES),
    _fixed("missing_device_stage", "run the device stage once for this device, or leave --device-results unset", MIXES),
    _fixed("outbox_unversioned", "move the records into a fingerprint folder or remove them", MIXES),
    _fixed("outbox_active_invalid", "rewrite the active pointer to an existing fingerprint folder", MIXES),
    _fixed("outbox_missing", "restore the outbox folder the active pointer names, or remove the pointer", MIXES),
    _fixed("outbox_fingerprint_invalid", "the fingerprint is not a charter hash; remove the folder", MIXES),
    _fixed("outbox_unkeyed", "remove the records the current items do not key", MIXES),
    _fixed("device_id_changed", "the device changed between identify and probe; rerun on one device", MIXES),
    _fixed("setup_mismatch", "restore the setup the line names, or set device.benchmark.onSetupMismatch: rerun to measure "
           "the whole benchmark again", MIXES),
    _fixed("not_benchmarked", "measure the gaps the line lists: rerun the guide with its device stage, or read "
           "log/details/benchmark_coverage.yaml", MIXES),
    _fixed("merge_refused", "the stored benchmark is kept whole; rerun the guide", MIXES),
    _fixed("device_not_in_results", PICK_DEVICE, MIXES),
    _fixed("several_device_results", PICK_DEVICE, MIXES),
    _fixed("no_device_results", "run the device stage, or point --results-root at a results root", MIXES),
    _fixed("not_device_results", "pass a device folder cryptobenchmark wrote", MIXES),
    _fixed("measured_mismatch", "rerun the app's device step", MIXES),
    _fixed("dossier_changed", "rerun with --refresh to ask the changed units again", MIXES),
    _fixed("schema_version", "rerun the step that writes the file", MIXES),
    _fixed("device_busy", "wait for the other run on the device folder to end", MIXES),
    # fixed: nothing is left to run
    _fixed("missing_results", "pass a device folder cryptobenchmark wrote", NOTHING),
    _fixed("several_project_roots", "pass one of the project roots as --app", NOTHING),
    _fixed("no_options", "see each scope's reason in dossiers.json noOptions", NOTHING),
    _fixed("no_replacement", "every scope is kept; nothing to edit", NOTHING),
    _fixed("no_edit_applied", "see each edit's reason in edits.json", NOTHING),
    _fixed("edit_invalid", STEP_LINES, NOTHING),
    _fixed("harness_invalid", STEP_LINES, NOTHING),
    _fixed("target_missing", "fix the apps.targets entry; its earlier results stay", NOTHING),
    _fixed("run_exists", "set onExisting to resume or overwrite, or name another run id", NOTHING),
    _fixed("no_targets", "fix apps.targets: no entry is an app; the skip lines above say why", NOTHING),
    *(_fixed(f"{s}_failed", STEP_LINES, NOTHING) for s in GUIDE_STEPS),
    _fixed("pipeline_failed", "read the transcript line the status names", NOTHING),
    _fixed("pipeline_timeout", "raise timeouts.pipeline, or check the device", NOTHING),
    _fixed("identify_failed", "run apps/benchmark-runner/pipeline.py --identify by hand to see why", NOTHING),
    _fixed("claude_cli_failed", "log in to the claude CLI, or check its binary and budget", NOTHING),
    _fixed("claude_cli_timeout", "raise timeouts.claude, or check the claude CLI", NOTHING),
    _fixed("claude_api_failed", "check ANTHROPIC_API_KEY and the API status", NOTHING),
    _fixed("claude_api_missing", "pip install -e '.[api]'", NOTHING),
    _fixed("bug", "the traceback is in log/bug.log; report it", NOTHING),
    # fixed: the input is unusable
    _fixed("missing_file", "pass a file that exists"),
    _fixed("invalid", FIX_SETTINGS),
    _fixed("invalid_yaml", "fix the YAML of the file the message names"),
    _fixed("secret_key", "move the secret to the environment or .env"),
    _fixed("missing_input", "set the input, or restore its packaged default"),
    _fixed("unknown_gateway", "name a registered gateway: claude or dry-run"),
    _fixed("missing_secret", "set the secret in the environment or .env"),
    _fixed("wrong_version", FIX_PROMPTS),
    _fixed("placeholder_missing", FIX_PROMPTS),
    _fixed("missing_directory", FIX_PROMPTS),
    _fixed("prompt_missing", FIX_PROMPTS),
    _fixed("prompt_unknown", FIX_PROMPTS),
    _fixed("value_mismatch", FIX_PROMPTS),
    _fixed("lifetime_mismatch", "a conversation was started out of order; report it"),
    _fixed("not_a_directory", "pass the app's source folder as --app"),
    _fixed("not_readable", "make the app folder readable"),
    _fixed("not_android_project", "pass a folder holding an Android project root"),
    _fixed("escapes_root", "remove the link that leaves the app folder"),
    _fixed("too_large", "pass a smaller project root"),
    _fixed("over_budget", "raise the budget the message names in perfrepair.yaml, or find why the item's message grew"),
    _fixed("bundled_catalog_yaml", FIX_CATALOG),
    _fixed("interchange_component", FIX_CATALOG),
    _fixed("interchange_key", FIX_CATALOG),
    _fixed("names_catalog_duplicate", FIX_CATALOG),
    _fixed("names_schema", FIX_CATALOG),
    _fixed("groups_invalid", FIX_CATALOG),
    _fixed("contracts_invalid", FIX_CATALOG),
    _fixed("groups_schema", FIX_CATALOG),
    _fixed("screening_schema", FIX_CATALOG),
    _fixed("screening_shape", FIX_CATALOG),
    _fixed("screening_yaml", FIX_CATALOG),
    _fixed("algorithms_invalid", FIX_CATALOG),
    _fixed("algorithm_unknown", "name an algorithm or group id the catalogues hold"),
    _fixed("relations_schema", FIX_CATALOG),
    _fixed("events_unreadable", "move the unreadable events.jsonl aside"),
    _fixed("journal_unreadable", "move the unreadable journal.jsonl aside; the outbox, not the journal, holds the decisions"),
    _fixed("item_not_configured", "rerun the device stage with the item in the run config"),
    _fixed("manifest_without_device_id", "rerun the benchmark"),
    _fixed("missing_effective", "rerun the device stage"),
    _fixed("missing_parameters", RERUN_INBOUND),
    _fixed("missing_probe", "rerun the device stage"),
    _fixed("missing_step", "run the app's earlier steps first"),
    _fixed("no_dossier", "rerun repair dossier, then repair edit, for the app"),
    _fixed("artifact_invalid", "read the problems the line lists; rerun the step that wrote the artifact"),
    _fixed("invariant_failed", "run python3 -m perfrepair.validation.invariants on the device folder; fix each blocking finding it prints"),
    _fixed("no_benchmark", "rerun the benchmark"),
    _fixed("delta_unconfigured", "restore the stored benchmark's config the line names, or rerun the device stage"),
    _fixed("no_events", "run a command against the device folder first"),
    _fixed("no_reports", "run the guide with --device first"),
    _fixed("no_screen", RERUN_GROUPING),
    _fixed("primitive_line_collision", RERUN_INBOUND),
    _fixed("primitive_not_screened", "grouping/items.json and the benchmark are from different runs; rerun the device stage"),
    _fixed("review_verdict", "fill the verdict column with one of the listed values"),
    _fixed("run_context", "report it"),
    _fixed("run_unknown", "name a run log summary lists"),
    # notices: warned, never a choice
    _fixed("unknown_key", "remove the key, or fix its spelling", NOTICE, action=WARN),
    _fixed("mixed_agents", "nothing; the records name each gateway", NOTICE, action=WARN),
    _fixed("alias_conflict", "nothing; a catalogued name keeps the catalog's function, any other is asked; settle the alias in algorithm-names.yaml", NOTICE,
           action=WARN),
    _fixed("perf_mode_extra", "drop the measurement from the run config to save device time", NOTICE, action=WARN),
    _fixed("append_repaired", "nothing; the partial line stays and readers skip it", NOTICE, action=WARN),
    _fixed("log_dropped", "name the device folder earlier in the command", NOTICE, action=WARN),
    _fixed("stop_fixed", "remove the stops.<code> entry", NOTICE, action=WARN),
    _fixed("interop_unverified", "the option stays and a replace to it declares unverified_interop; only a line naming a missing device or config has a fix: make it and rerun the guide",
           NOTICE, action=WARN),
)
CODES: dict[str, Code] = {c.code: c for c in CODES_LIST}
OVERRIDABLE = tuple(c for c in CODES_LIST if not c.fixed)
