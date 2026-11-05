# Stops

## Terminate

- `stop/codes.py` holds every stop, warn and skip code once; `stop/terminate.py` `terminate(code, detail, ...)` is where an overridable code's action is decided. `terminate` resolves the action, emits one `finding` event with `data.code`, `data.action` and `data.next` (its `status.log` line), then raises `Halt(code, detail, next_step)` on `stop`, or returns `warn` (the item kept) or `skip` (left out and counted) to its caller.
- `failure.py` maps a `Halt` to its code's exit; any other coded failure is one `error` event with `data.code`; a step that ends in a `Halt` records `data.reported` on its end, and `status.log` shows the `terminate` line only. A guide step's other coded failure is `<step>_failed`, the inner code in `data.inner` and first in the detail; a command another one runs in-process writes no `error` event of its own, and its caller's `<step>_failed` line carries its code. When that inner code is `primitive_not_screened`, `data.next` is `read <device>/log/details/primitives_missing.yaml; ` and that code's own next, in place of the generic one below ([run-log.md](run-log.md)). A code with no `Halt` yet is a coded exception whose `.code` `failure.py` records; a failure with no `.code` has no code.

## Settings

| key | values | on a bad value |
|---|---|---|
| `stops.<code>` of an overridable code | the code's allowed actions below | one warning `invalid: stops.<code> <value>, one of [...]; using the default <default>`, then the default |
| `stops.<code>` of a fixed code | none | one warning `stop_fixed: stops.<code> <value>, <code> is fixed (<why>); ignored` when the code fires |
| `device.bundled.onMissing` | `warn`, `stop` | the same as `stops.bundled_missing`; read only when `stops.bundled_missing` is unset |

- Each key is read when its code fires, through its `inputs/table.py` row (`STOP_ROWS`), by `config/stops.py`; the first command of a run that loads settings installs the reader; a command it runs in-process keeps it; without one each code takes its default.

## Codes

Exit: what `failure.py` returns for the code; argparse refusals exit 2 before any code is reached.

| code | default | `stops.<code>` | exit | next |
|---|---|---|---|---|
| `bundled_missing` | `warn` | `warn`, `stop` | 1 | add the providers to providers.bundled in global.yaml, or set device.bundled.fromApps |
| `not_on_device` | `warn` | `warn`, `stop` | 1 | add it to providers.bundled in global.yaml and rerun the device stage |
| `perf_mode_unmeasured` | `stop` | `stop`, `warn` | 1 | measure on a device (guide --device), or drop the metric from apps.perfMode |
| `perf_mode_maybe_unmeasured` | `warn` | `warn`, `stop` | 1 | set run.harness.energy.capture: measured, or rely on the test set |
| `energy_invalid` | `warn` | `warn`, `stop` | 1 | the case has no energy number; rerun it with a longer window or more operations |
| `energy_unreadable` | `warn` | `warn`, `stop` | 1 | check the energy.json files the manifest lists |
| `thermal_mismatch` | `warn` | `warn`, `stop` | 1 | the sides of a pair started at different temperatures; rerun the pair, or read its ratio with care |
| `category_mismatch` | `warn` | `warn`, `stop` | 1 | the before/after disagrees with its category's estimate; check the scope's pattern against its function, or read its ratio with care |
| `thermal_throttled_at_end` | `warn` | `warn`, `stop` | 1 | the case ended throttled; let the phone cool, or read its numbers with care |
| `no_required_metric` | `skip` | `skip`, `stop` | 1 | the case has no required metric runs; check the benchmark transcript |
| `invariant_undecided` | `warn` | `warn`, `stop` | 1 | the source does not decide a rule; run python3 -m perfrepair.validation.invariants on the device folder and check each undecided finding by hand |
| `run_metrics_overridden` | `warn` | fixed: a notice; nothing to choose | 1 | remove run.metrics from the run config; apps.perfMode decides what is measured |
| `missing_dependency` | `stop` | fixed: the input is unusable | 1 | pip install -r requirements.txt |
| `screening_catalog_mismatch` | `stop` | fixed: continuing would mix runs or devices | 1 | rerun grouping build, or set device.screening.catalog to the catalog screen.json names |
| `charter_mismatch` | `stop` | fixed: continuing would mix runs or devices | 1 | move the outbox aside or restore the prompts it was made with |
| `missing_device_stage` | `stop` | fixed: continuing would mix runs or devices | 1 | run the device stage once for this device, or leave --device-results unset |
| `outbox_unversioned` | `stop` | fixed: continuing would mix runs or devices | 1 | move the records into a fingerprint folder or remove them |
| `outbox_active_invalid` | `stop` | fixed: continuing would mix runs or devices | 1 | rewrite the active pointer to an existing fingerprint folder |
| `outbox_missing` | `stop` | fixed: continuing would mix runs or devices | 1 | restore the outbox folder the active pointer names, or remove the pointer |
| `outbox_fingerprint_invalid` | `stop` | fixed: continuing would mix runs or devices | 1 | the fingerprint is not a charter hash; remove the folder |
| `outbox_unkeyed` | `stop` | fixed: continuing would mix runs or devices | 1 | remove the records the current items do not key |
| `device_id_changed` | `stop` | fixed: continuing would mix runs or devices | 1 | the device changed between identify and probe; rerun on one device |
| `setup_mismatch` | `stop` | fixed: continuing would mix runs or devices | 1 | restore the setup the line names, or set device.benchmark.onSetupMismatch: rerun to measure the whole benchmark again |
| `not_benchmarked` | `stop` | fixed: continuing would mix runs or devices | 1 | measure the gaps the line lists: rerun the guide with its device stage, or read log/details/benchmark_coverage.yaml |
| `merge_refused` | `stop` | fixed: continuing would mix runs or devices | 1 | the stored benchmark is kept whole; rerun the guide |
| `device_not_in_results` | `stop` | fixed: continuing would mix runs or devices | 1 | pass --device-results or set device.id |
| `several_device_results` | `stop` | fixed: continuing would mix runs or devices | 1 | pass --device-results or set device.id |
| `no_device_results` | `stop` | fixed: continuing would mix runs or devices | 1 | run the device stage, or point --results-root at a results root |
| `not_device_results` | `stop` | fixed: continuing would mix runs or devices | 1 | pass a device folder cryptobenchmark wrote |
| `measured_mismatch` | `stop` | fixed: continuing would mix runs or devices | 1 | rerun the app's device step |
| `dossier_changed` | `stop` | fixed: continuing would mix runs or devices | 1 | rerun with --refresh to ask the changed units again |
| `schema_version` | `stop` | fixed: continuing would mix runs or devices | 1 | rerun the step that writes the file |
| `device_busy` | `stop` | fixed: continuing would mix runs or devices | 1 | wait for the other run on the device folder to end |
| `missing_results` | `stop` | fixed: nothing is left to run | 1 | pass a device folder cryptobenchmark wrote |
| `several_project_roots` | `stop` | fixed: nothing is left to run | 1 | pass one of the project roots as --app |
| `no_options` | `stop` | fixed: nothing is left to run | 1 | see each scope's reason in dossiers.json noOptions |
| `no_replacement` | `stop` | fixed: nothing is left to run | 1 | every scope is kept; nothing to edit |
| `no_edit_applied` | `stop` | fixed: nothing is left to run | 1 | see each edit's reason in edits.json |
| `edit_invalid` | `stop` | fixed: nothing is left to run | 1 | read the lines the step printed above; fix and rerun the guide |
| `harness_invalid` | `stop` | fixed: nothing is left to run | 1 | read the lines the step printed above; fix and rerun the guide |
| `target_missing` | `stop` | fixed: nothing is left to run | 1 | fix the apps.targets entry; its earlier results stay |
| `run_exists` | `stop` | fixed: nothing is left to run | 1 | set onExisting to resume or overwrite, or name another run id |
| `no_targets` | `stop` | fixed: nothing is left to run | 1 | fix apps.targets: no entry is an app; the skip lines above say why |
| `prerequisites_failed` | `stop` | fixed: nothing is left to run | 1 | read the lines the step printed above; fix and rerun the guide |
| `targets_failed` | `stop` | fixed: nothing is left to run | 1 | read the lines the step printed above; fix and rerun the guide |
| `grouping_failed` | `stop` | fixed: nothing is left to run | 1 | read the lines the step printed above; fix and rerun the guide |
| `interop_failed` | `stop` | fixed: nothing is left to run | 1 | read the lines the step printed above; fix and rerun the guide |
| `detect_failed` | `stop` | fixed: nothing is left to run | 1 | read the lines the step printed above; fix and rerun the guide |
| `app_failed` | `stop` | fixed: nothing is left to run | 1 | read the lines the step printed above; fix and rerun the guide |
| `dossier_failed` | `stop` | fixed: nothing is left to run | 1 | read the lines the step printed above; fix and rerun the guide |
| `replace_failed` | `stop` | fixed: nothing is left to run | 1 | read the lines the step printed above; fix and rerun the guide |
| `edit_failed` | `stop` | fixed: nothing is left to run | 1 | read the lines the step printed above; fix and rerun the guide |
| `harness_failed` | `stop` | fixed: nothing is left to run | 1 | read the lines the step printed above; fix and rerun the guide |
| `device_failed` | `stop` | fixed: nothing is left to run | 1 | read the lines the step printed above; fix and rerun the guide |
| `report_failed` | `stop` | fixed: nothing is left to run | 1 | read the lines the step printed above; fix and rerun the guide |
| `summary_failed` | `stop` | fixed: nothing is left to run | 1 | read the lines the step printed above; fix and rerun the guide |
| `pipeline_failed` | `stop` | fixed: nothing is left to run | 1 | read the transcript line the status names |
| `pipeline_timeout` | `stop` | fixed: nothing is left to run | 1 | raise timeouts.pipeline, or check the device |
| `identify_failed` | `stop` | fixed: nothing is left to run | 1 | run apps/benchmark-runner/pipeline.py --identify by hand to see why |
| `claude_cli_failed` | `stop` | fixed: nothing is left to run | 1 | log in to the claude CLI, or check its binary and budget |
| `claude_cli_timeout` | `stop` | fixed: nothing is left to run | 1 | raise timeouts.claude, or check the claude CLI |
| `claude_api_failed` | `stop` | fixed: nothing is left to run | 1 | check ANTHROPIC_API_KEY and the API status |
| `claude_api_missing` | `stop` | fixed: nothing is left to run | 1 | pip install -e '.[api]' |
| `bug` | `stop` | fixed: nothing is left to run | 1 | the traceback is in log/bug.log; report it |
| `missing_file` | `stop` | fixed: the input is unusable | 1 | pass a file that exists |
| `invalid` | `stop` | fixed: the input is unusable | 1 | fix the value in perfrepair.yaml, the environment or the flag the message names |
| `invalid_yaml` | `stop` | fixed: the input is unusable | 1 | fix the YAML of the file the message names |
| `secret_key` | `stop` | fixed: the input is unusable | 1 | move the secret to the environment or .env |
| `missing_input` | `stop` | fixed: the input is unusable | 1 | set the input, or restore its packaged default |
| `unknown_gateway` | `stop` | fixed: the input is unusable | 1 | name a registered gateway: claude or dry-run |
| `missing_secret` | `stop` | fixed: the input is unusable | 1 | set the secret in the environment or .env |
| `wrong_version` | `stop` | fixed: the input is unusable | 1 | fix the prompts folder or prompts.yaml the message names |
| `placeholder_missing` | `stop` | fixed: the input is unusable | 1 | fix the prompts folder or prompts.yaml the message names |
| `missing_directory` | `stop` | fixed: the input is unusable | 1 | fix the prompts folder or prompts.yaml the message names |
| `prompt_missing` | `stop` | fixed: the input is unusable | 1 | fix the prompts folder or prompts.yaml the message names |
| `prompt_unknown` | `stop` | fixed: the input is unusable | 1 | fix the prompts folder or prompts.yaml the message names |
| `value_mismatch` | `stop` | fixed: the input is unusable | 1 | fix the prompts folder or prompts.yaml the message names |
| `lifetime_mismatch` | `stop` | fixed: the input is unusable | 1 | a conversation was started out of order; report it |
| `not_a_directory` | `stop` | fixed: the input is unusable | 1 | pass the app's source folder as --app |
| `not_readable` | `stop` | fixed: the input is unusable | 1 | make the app folder readable |
| `not_android_project` | `stop` | fixed: the input is unusable | 1 | pass a folder holding an Android project root |
| `escapes_root` | `stop` | fixed: the input is unusable | 1 | remove the link that leaves the app folder |
| `too_large` | `stop` | fixed: the input is unusable | 1 | pass a smaller project root |
| `over_budget` | `stop` | fixed: the input is unusable | 1 | raise the budget the message names in perfrepair.yaml, or find why the item's message grew |
| `bundled_catalog_yaml` | `stop` | fixed: the input is unusable | 1 | fix the catalog file the message names |
| `interchange_component` | `stop` | fixed: the input is unusable | 1 | fix the catalog file the message names |
| `interchange_key` | `stop` | fixed: the input is unusable | 1 | fix the catalog file the message names |
| `names_catalog_duplicate` | `stop` | fixed: the input is unusable | 1 | fix the catalog file the message names |
| `names_schema` | `stop` | fixed: the input is unusable | 1 | fix the catalog file the message names |
| `groups_invalid` | `stop` | fixed: the input is unusable | 1 | fix the catalog file the message names |
| `contracts_invalid` | `stop` | fixed: the input is unusable | 1 | fix the catalog file the message names |
| `groups_schema` | `stop` | fixed: the input is unusable | 1 | fix the catalog file the message names |
| `screening_schema` | `stop` | fixed: the input is unusable | 1 | fix the catalog file the message names |
| `screening_shape` | `stop` | fixed: the input is unusable | 1 | fix the catalog file the message names |
| `screening_yaml` | `stop` | fixed: the input is unusable | 1 | fix the catalog file the message names |
| `algorithms_invalid` | `stop` | fixed: the input is unusable | 1 | fix the catalog file the message names |
| `algorithm_unknown` | `stop` | fixed: the input is unusable | 1 | name an algorithm or group id the catalogues hold |
| `relations_schema` | `stop` | fixed: the input is unusable | 1 | fix the catalog file the message names |
| `events_unreadable` | `stop` | fixed: the input is unusable | 1 | move the unreadable events.jsonl aside |
| `journal_unreadable` | `stop` | fixed: the input is unusable | 1 | move the unreadable journal.jsonl aside; the outbox, not the journal, holds the decisions |
| `item_not_configured` | `stop` | fixed: the input is unusable | 1 | rerun the device stage with the item in the run config |
| `manifest_without_device_id` | `stop` | fixed: the input is unusable | 1 | rerun the benchmark |
| `missing_effective` | `stop` | fixed: the input is unusable | 1 | rerun the device stage |
| `missing_parameters` | `stop` | fixed: the input is unusable | 1 | rerun the inbound stage (or the guide's device stage) |
| `missing_probe` | `stop` | fixed: the input is unusable | 1 | rerun the device stage |
| `missing_step` | `stop` | fixed: the input is unusable | 1 | run the app's earlier steps first |
| `no_dossier` | `stop` | fixed: the input is unusable | 1 | rerun repair dossier, then repair edit, for the app |
| `artifact_invalid` | `stop` | fixed: the input is unusable | 1 | read the problems the line lists; rerun the step that wrote the artifact |
| `invariant_failed` | `stop` | fixed: the input is unusable | 1 | run python3 -m perfrepair.validation.invariants on the device folder; fix each blocking finding it prints |
| `no_benchmark` | `stop` | fixed: the input is unusable | 1 | rerun the benchmark |
| `delta_unconfigured` | `stop` | fixed: the input is unusable | 1 | restore the stored benchmark's config the line names, or rerun the device stage |
| `no_events` | `stop` | fixed: the input is unusable | 1 | run a command against the device folder first |
| `no_reports` | `stop` | fixed: the input is unusable | 1 | run the guide with --device first |
| `no_screen` | `stop` | fixed: the input is unusable | 1 | rerun grouping build, assign and report |
| `primitive_line_collision` | `stop` | fixed: the input is unusable | 1 | rerun the inbound stage (or the guide's device stage) |
| `primitive_not_screened` | `stop` | fixed: the input is unusable | 1 | grouping/items.json and the benchmark are from different runs; rerun the device stage |
| `review_verdict` | `stop` | fixed: the input is unusable | 1 | fill the verdict column with one of the listed values |
| `run_context` | `stop` | fixed: the input is unusable | 1 | report it |
| `run_unknown` | `stop` | fixed: the input is unusable | 1 | name a run log summary lists |
| `unknown_key` | `warn` | fixed: a notice; nothing to choose | 1 | remove the key, or fix its spelling |
| `mixed_agents` | `warn` | fixed: a notice; nothing to choose | 1 | nothing; the records name each gateway |
| `alias_conflict` | `warn` | fixed: a notice; nothing to choose | 1 | nothing; a catalogued name keeps the catalog's function, any other is asked; settle the alias in algorithm-names.yaml |
| `perf_mode_extra` | `warn` | fixed: a notice; nothing to choose | 1 | drop the measurement from the run config to save device time |
| `append_repaired` | `warn` | fixed: a notice; nothing to choose | 1 | nothing; the partial line stays and readers skip it |
| `log_dropped` | `warn` | fixed: a notice; nothing to choose | 1 | name the device folder earlier in the command |
| `stop_fixed` | `warn` | fixed: a notice; nothing to choose | 1 | remove the stops.<code> entry |
| `interop_unverified` | `warn` | fixed: a notice; nothing to choose | 1 | the option stays and a replace to it declares unverified_interop; only a line naming a missing device or config has a fix: make it and rerun the guide |
