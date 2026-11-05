# Repair

## Calls
- `docs/repair.md` : steps, inputs, outputs, limits
- `docs/replacement.md` : the flow from scope to measured before/after

## Rules
- scope: the model's choice is the worthiness verdict's pair; everything here is a static join, rewrite or report.
- edit: apply by exact span only; a span that cannot be re-found or read is a coded rejection, never a guess.
- edit: never write inside the app root; copies go to `<app>/original/` and `patched/`.
- edit: a splice keeps the file's line count; harness extraction relies on it.
- edit: never edit a constant's declaration or render code from model text; constants come from `specs.yaml`.
- edit: atomic over a unit's replaced members: one rejected member rejects them all, and the other rows say which and why; a member that stays has no edit.
- edit: a new reason code goes in `EDIT_REASONS` (`validation/repair.py`) and the limits table of `docs/repair.md`.
- pin: a new parameter spec is a row in `specs.yaml`, never code.
- order: scope → dossier → test-set (per-app benchmark run) → replace → edit → harness → device → report.
- guide: `guide/device_steps.py` and `guide/app_steps.py` chain the stage functions and commands; they add no logic of their own and stop at the first failing step with a coded reason.
- report: a number says its kind, `function` or `callSite`; the verdict uses the function's when present.
- report: never invent a number; a metric without both runs is `not measured` with the first step that stopped it.
- change class: code classes a candidate and offers those up to `apps.maxChange`; the model selects, the gate refuses a pick above it; the higher ones stay recommendations.

## File structure

```
src/perfrepair/__main__.py : command: `python3 -m perfrepair guide`; dispatch only
src/perfrepair/failure.py : FAILURES and reported: every command's failure as one `error ...` line and its code's exit; a Halt adds no event (terminate wrote it), another coded failure one error event with data.code, none when run in-process (last_failure hands it to the caller)
src/perfrepair/guide/app_steps.py : the steps for one app: app, dossier, replace, edit, harness, device, report; their stop codes
src/perfrepair/guide/command.py : guide arguments, among them --run-id, --on-existing, --harness-config, --stop-after-device, --outcome, --run-settings; `--app` or apps.targets, the one reader of that row, resolved by `app/facts/target_set.py`: skip lines, root warnings, no_targets; device.filterByApps's reader
src/perfrepair/guide/device_steps.py : the device-level steps: interop (the pair check, its counts and coded lines); prerequisites (the RunRecord opened once the folder is known, run_exists and device_busy; probe_device when no folder is named; with device.filterByApps the targets' detect and used.json, else used.json removed), detect_targets, targets (target_file.py), grouping (coverage: reused, or assign and report for what is missing), the benchmark gate after the used set and after grouping (gate_steps.py), summary; their stop codes
src/perfrepair/guide/finished.py : the inputs an app's done mark is compared with: digests of its tree, scopes, units, the perf-repair code from tree to harness.yaml, the host's harness digest (`--identify`), the device files, and when measured its harness config; code_versions: both code digests, read once per run, an empty source a coded error
src/perfrepair/guide/gate_steps.py : the guide's two gate points: the used set (made again after grouping), or the measured plan with device.filterByApps off, the gate's policy from device.benchmark.onGap and onSetupMismatch, the command --device-results prints, the coverage rows on primitives_missing.yaml
src/perfrepair/guide/index.py : <device>/apps-index.tsv, written by the summary step and on demand: per app folder its project (rootProject.name, else its path under the apps' common folder), source, sites, scopes, scopes per pattern and unknown_default, stage reached (its files in guide order, none older than the one before; later columns only within it), the latest run's stop code and reason, options per change class and track, notOffered, chosen replaces, measured
src/perfrepair/guide/outcome.py : --outcome: the device folder, run id, exit and code a guide run's caller reads
src/perfrepair/guide/run.py : one status line and event per step, the first stop ends the sequence, the dry-run ending; Stopped (halts: a provider failure)
src/perfrepair/guide/settings_tree.py : perfrepair.yaml and its pointers through their real parsers for the facade's check, unknown keys refused; the packaged catalogs
src/perfrepair/guide/state.py : Guide settings, the running step, the run's RunRecord, the units a cap left and whether a gate merged a delta (replace then asks changed dossiers again); halt and check_exit, a step's coded stop
src/perfrepair/guide/target_file.py : the targets step: <device>/targets.yaml before any model step, removed with --app; a non-app path entry's stop
src/perfrepair/guide/targets.py : the loop: device-level steps once, each app isolated and reused by its RunRecord, terminal and incomplete outcomes recorded, the report summary, one line per app (a non-app path entry's stop first), Ctrl-C after the summary, the exit rule
src/perfrepair/repair/__main__.py : command: dossier | test-set | edit | harness, each `--device-results --app`; `--perfrepair-config` fills the folder and the screening catalog
src/perfrepair/repair/call_site.py : a scope's callSite for harness.yaml: the one operation from its lifecycle, else from the chosen option's estimates; its pattern as the variant
src/perfrepair/repair/dependencies.py : identifiers a function uses but does not define, from tokens; a numeric literal is one token
src/perfrepair/repair/dossier.py : command step: scopes + groups + measurements + the given screening Catalog (refused unless screen.json recorded it) at app.json's targetSdk, under the app's perfMode → <app>/dossiers.json, validated before writing; counts no_evidence scopes
src/perfrepair/repair/edit/__init__.py : re-exports edit_app, load_specs and the source helpers harness reads: read_source, language, function_lines, import_lines
src/perfrepair/repair/edit/algorithm.py : set_algorithm: the literal algorithm argument rewritten
src/perfrepair/repair/edit/alone.py : units applied in one function: a copy of the file per unit with only its splices
src/perfrepair/repair/edit/app.py : an app's replace decisions applied to copies, atomically over each unit's replaced members; edits.json document
src/perfrepair/repair/edit/init.py : the one init call on the engine a scope's call returns
src/perfrepair/repair/edit/lines.py : whole lines of a source: a function's line range, its import lines
src/perfrepair/repair/edit/literal.py : a string rendered as a Java or Kotlin literal
src/perfrepair/repair/edit/locate.py : a scope's function span and its call re-found with the scope step's lexer; argument spans or a coded rejection
src/perfrepair/repair/edit/parameters.py : pin_parameters: the init's parameter spec rendered or its pinned fields overridden
src/perfrepair/repair/edit/plan.py : one scope's edits turned into splices through the kind → apply function table, or a coded rejection
src/perfrepair/repair/edit/provider.py : set_provider: the provider argument rewritten or appended
src/perfrepair/repair/edit/reject.py : the coded rejection an edit raises
src/perfrepair/repair/edit/specs.py : specs.yaml loaded: spec choice by pinned fields, field rendering
src/perfrepair/repair/edit/specs.yaml : JCA parameter specs: constructor arguments, field types, defaults, render templates
src/perfrepair/repair/edit/splice.py : exact-span replacement that keeps line numbers; unified diff
src/perfrepair/repair/harness.py : harness.yaml: each applied scope's original and patched function, the imports it uses, inputs, current and option item, dependencies, notMeasurable
src/perfrepair/repair/imports.py : the import lines a scope's functions use by name; a wildcard only while a name is unresolved
src/perfrepair/repair/inputs.py : a scope's harness inputs: the app's static sizes, else the run's effective.yaml sizes both items share; their source
src/perfrepair/repair/inverses.py : each applied scope's interop partner, from the inverse links of units.json
src/perfrepair/repair/names.yaml : keywords, primitive types and implicit names per language; java.lang of android.jar, compared with apps/benchmark-runner/scope/languages.py by a test
src/perfrepair/repair/operation.py : whether a scope's function calls an operation on its primitive: `no_operation` for a factory
src/perfrepair/repair/setup_calls.yaml : member calls that only configure a primitive; Kotlin scope-function blocks
src/perfrepair/repair/test_set.py : dossiers.json → cryptobenchmark test set: each scope's current item and every option
src/perfrepair/report/__main__.py : command: `app --device-results --app [--perf-mode]` | `summary --device-results`
src/perfrepair/report/app_report.py : an app's step files → report.json: a row per scope with its unit and the members that stayed, the funnel
src/perfrepair/report/command.py : stage: report.json and .md, summary.json and .md, validated before writing; thermal labels and category_mismatch through the terminator
src/perfrepair/report/markdown.py : report.md and summary.md from their documents; time in the report's units, one row and its throughput line; each row's pattern; the summary's categories table and a section per category
src/perfrepair/report/measured.py : cryptobenchmark's scoped-plan.yaml and scoped benchmark.json for one app; refuses a plan of another harness
src/perfrepair/report/metrics.py : before and after cases → per metric, each marked selected or not: medians, ratio, pImprove, level through compare(); the time metric's latency and throughput views in the display units
src/perfrepair/report/recommendations.py : dossiers.json's notOffered → recommendations above maxChange, never applied, and reject counts; their sum for the summary
src/perfrepair/report/scope_row.py : one scope's pattern, decision, edit, compile, interop; its function and call-site numbers, each with verdict, label, thermal and truth check; measuredBy, the kind the row's verdict uses
src/perfrepair/report/summary.py : report.json files → summary.json: funnel sums, pattern counts, and per pattern apart: apps improved, unchanged, worse per selected metric, labels, swaps
src/perfrepair/report/swaps.py : the rows of every app → one view per chosen swap across its apps, and the replace decisions per label
src/perfrepair/report/thermal.py : a before/after pair's `thermal` blocks and sleeps, their start gap and labels
src/perfrepair/review/__init__.py : docstring only
src/perfrepair/review/__main__.py : command: `sheet|score <device>`, `stability <device> --sample N --asks K`
src/perfrepair/review/score.py : the sheet's verdicts and the journals' turns → grouping precision, pick accuracy, stability across asks of one message, gate rejections per 100 calls; review/score.json
src/perfrepair/review/sheet.py : one row per model decision from the active outboxes with its scope pattern and patternReason, code facts, pick, reason, empty verdict and note: review/decisions.tsv; a rebuild keeps what a person filled
src/perfrepair/review/stability.py : StabilityKind: N sampled replace units asked K times each on the engine, on the message `ai replace` sends → review/stability.json, its outbox in review/stability
```
