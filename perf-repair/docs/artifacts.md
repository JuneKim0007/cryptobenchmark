# Artifacts

- One device folder, `<results root>/<device id>/`, holds every artifact and the benchmark's own files ([results.md](../../docs/results.md)), except the `repair test-set` YAML (its `-o` path).
- Device-level artifacts sit in the folder; per-app ones in `<device>/<app>/`.

## Folders

| item | rule |
|---|---|
| `--device-results` | the device folder, on every command |
| `paths.results` | the root, used when the flag is unset: `device.id` names the folder, else its only device |
| a device | a folder holding `manifest.yaml`; a run that failed and `.staging-*` are not |
| `<app>` | `--app <path>` gives `<dirname>-<8 hex of sha256 of the absolute path>` (`app/facts/path_id.py`); `app.json` records it as `pathId`, the absolute path as `root` |
| several project roots | one `<app>.<root dirs joined by '.'>` per root; `root` is that project root; a later command takes that root as `--app` and finds the unit by `app.json` |
| an old manifest | `manifest_without_device_id; rerun the benchmark` |
| a results folder under `/tmp`, `/var/tmp`, `/var/folders` or the system temp folder | one warning `results_in_temp: ...`, then the command goes on |

| error | when |
|---|---|
| `several_device_results: <root> holds a, b; set device.id or pass --device-results` | several devices and no `device.id` |
| `device_not_in_results: <id>; <root> holds [...]` | `device.id` names no finished device under the root |
| `no_device_results: <root> ...` | the root holds no finished device |
| `not_device_results: <folder> has no manifest.yaml; pass <root>/<device id>` | `--device-results` names a root holding devices, or a command reads the manifest of a folder without one |

## Files

| Artifact | Producer | Consumers | Validator |
|---|---|---|---|
| `manifest.yaml` | cryptobenchmark `pipeline.py` | inbound, grouping build, probe_device (`inputs`); `units` by `display_units` for the report and both renders (absent: ms, MB/s) | `validation/manifest.py` |
| `device.yaml` | probe_device, last | probe_device | `DeviceRecord.from_json`: schema, the four input digests, the manifest's sha256; `benchmark`, after a used-set benchmark: the generated config's digest, the measured set's digest and items; `bundled`, with `device.bundled.fromApps: apply`: the applied entries' digest and the manifest's `bundled` and `config` digests they produced; unreadable counts as absent |
| `rows.json` | inbound | worthiness, validation | `validation/rows.py`: schema 2, every row's `variant` `fixed` or `notFixed` (a benchmark case without one is the legacy `notFixed`; `null`, a scoped before/after case, is refused) and `perCall` from `prepared.yaml` |
| `measurements.json` | inbound | worthiness, validation | `validation/measurements.py` |
| `run_log.json` | inbound | validation | `validation/run_log.py` |
| `primitives.tsv` | the device stage's primitives step (`device/primitives.py`) | `data_handler/inbound/primitives.py`; people | `validation/primitives.py`, before writing |
| `used.json` | the device stage's used step (`device/used.py`), with `device.filterByApps` | grouping assign and report (what is asked, `notUsed`), the benchmark's selection | `validation/used.py`, before writing; [Used set](#usedjson) |
| `metrics-global.yaml` | the device stage when the base `global.yaml` does not say what perfMode decided, removed otherwise; in `<app>/` for the per-app device step | every later config of the device stage; cryptobenchmark `pipeline.py --config` | none: the base with `run.metrics` decided ([pipeline.md](pipeline.md#device-stage)) |
| `used-global.yaml` | the device stage, before a benchmark of the used set | cryptobenchmark `pipeline.py --config` | none: the base `global.yaml` with `selection.exclude` added |
| `bundled-suggestions.yaml` | the device stage's bundled step (`device/bundled.py`), with `device.bundled.fromApps` `suggest` or `apply`; removed with `off` | people; `device/bundled_config.py`, for the per-app harness | `validation/bundled.py`, before writing and in `check` |
| `bundled-global.yaml` | the bundled step with `apply` and a row applied, removed otherwise; in `<app>/` when `apps.benchmarkConfig` is set | `used-global.yaml`; the per-app harness; cryptobenchmark `pipeline.py --config` | none: the base `global.yaml` with the applied entries after its own `providers.bundled` |
| `<app>/sites.json` | `perfrepair.app` | scope, used | none |
| `<app>/app.json` | `perfrepair.app` | dossier | `validation/app.py`, before writing |
| `<app>/scopes.json` | `perfrepair.app` | dossier, harness | `validation/app.py`, before writing: schema 5, every scope's lifecycle in its closed lists, its pattern the rule's for that lifecycle, cited lines inside the file |
| `<app>/units.json` | `perfrepair.app` | dossier, edit, harness, report, the guide's `finished.json` | `validation/units.py`, before writing: every scope in one unit, recomputed ids, members connected by their links, each cited line in that side's lifecycle |
| `grouping/*` | grouping | worthiness and repair read `groups.json` | `validation/grouping/*`; files: `docs/grouping.md` |
| `worthiness-<mode>/evidence.json` | worthiness | audit | none |
| `worthiness-<mode>/outbox/<fingerprint>/NNNNNN.json`, `outbox/active` | worthiness | worthiness (resume), validation | the commit; `WorthinessKind.validate` |
| `targets.yaml` | the guide's targets step, before grouping | people | none: written whole from `apps.targets` resolved ([targets.md](targets.md#targetsyaml)) |
| `<app>/finished.json` | `RunRecord.app_done`, when an app is done ([replacement.md](replacement.md)); removed on the first step of its rerun | `RunRecord.is_done` | none: `{schemaVersion: 1, inputs, outcome}`; inputs compared, anything else, unreadable included, is not done |
| `runs/run_<id>.json` | `RunRecord` (`run_dir/run_record.py`), written durably after the device stage and each app step | people | none: [Run record](#run-record) |
| `.lock` | the guide and probe_device(), `fcntl.flock`, the holder's pid | a second run: `device_busy` | none |
| `*/outbox/<fingerprint>/charter.json` | the engine, when it opens the outbox | the engine (`charter_mismatch`), validation | `check/device.py`: rehashed to the folder's name |
| `grouping/supervisor.charter.json` | grouping report --supervisor | validation | `check/device.py`: rehashed to `supervisor.json` `charter` |
| `log/events.jsonl` | every command, appended | watch, log summary, the views | `validation/events.py` |
| `log/status.log`, `log/ai/<stage>.log`, `log/bug.log` | the event sink, from the same events | people, log summary (status) | none: `log/views.py` renders them; [run-log.md](run-log.md) |
| `log/pipeline/<run id>.log` | `benchmark_runner.py`, appended per `pipeline.py` call | people, a `pipeline_failed` finding's ref | none |
| `worthiness-<mode>/verdicts.json` | worthiness | validation | `validation/verdicts.py` + projection equality |
| `worthiness-<mode>/journal.jsonl`, `errors.jsonl` | worthiness | audit | none |
| `<app>/dossiers.json` | repair dossier | replace, repair test-set | `validation/dossiers/`, before writing: schema 7 (estimates of the scope's pattern's variant only, `perCall`), `units` the units asked, `perfMode` the selection its estimates hold, `measured` the selected metrics the run has a measurement of, `maxChange`, `notOffered` the candidates rejected or above it, each with `outputChanges`; every option with `track`, `outputChanges`, `reach`, `needsReview` ([change-classes.md](change-classes.md#review-facts)) |
| `<app>/edits.json`, `original/`, `patched/`, `patched-alone/<unit>/` | repair edit | repair harness | `validation/repair.py`, before writing |
| `<app>/harness.yaml`, `harness/<scope>/` | repair harness | cryptobenchmark | `validation/repair.py`, before writing |
| `<app>/measured/` | cryptobenchmark `pipeline.py --device --harness` | report | cryptobenchmark |
| `<app>/report.json`, `report.md` | report app | report summary | `validation/report.py` and `validation/report_metrics.py`, before writing |
| `summary.json`, `summary.md` | report summary | people | `validation/summary.py`, before writing |
| `apps-index.tsv` | the guide's summary step, `perfrepair.guide.index` | people: find an app, what is left on it; its `fixed`, `notFixed` and `unknown_default` scope counts | none: rebuilt whole from the app folders and `log/events.jsonl` |
| `review/decisions.tsv` | the guide's summary step, `perfrepair.review` | people, `review score` | none: a verdict is `ok`, `wrong` or empty, checked by `score` |
| `review/score.json` | `perfrepair.review score` | people | none |
| `review/stability.json` | `perfrepair.review stability` | people | none |
| test-set YAML (`-o`) | repair test-set | cryptobenchmark | none |

- Every JSON document carries `schemaVersion`: 1, except `measurements.json` at 4 (each summary adds `low`, `high`: the median's 95% bootstrap interval, `null` below 2 runs; and `processes`: its runs per process; 4 keys every metric by its benchmark.json name, `allocations` became `allocationCount`), `worthiness-<mode>/evidence.json` at 3 (2: a member's summary per metric, a pair's comparison per metric; 3: only the perfMode's metrics), `<app>/dossiers.json` at 7 and `report.json`, `summary.json` at 6 (`selected` per metric row; summary metrics are the selected ones; `maxChange`, `recommendations`, `rejected`).
- A journal is append-only, one line per model turn with its `durationMs`, audit only; state is the projection of the outbox.
- `charter.json` holds the system and correction texts, the schema, the inputs and each prompt's `source` (`packaged` or the override path); an outbox from before it gets it on its next open.
- `measurements.json` carries the run's `runtime` and `comparability` notes; per row a summary for every metric of `dto/metrics.py` it has runs of, under its benchmark.json name (`timeNs` always); one with kinds (`energyJ`) carries its `kind`.
- An older `measurements.json` is unreadable: the device stage reruns inbound (`measurements.json unreadable (...)`).
- `check/grouping.py` rebuilds evidence from rows, measurements and `groups.json` to check verdicts.

## Run record

`runs/run_<id>.json`: one guide run on the device folder; `run.id` names it ([settings.md](settings.md)), unset a new `YYYYMMDDTHHMMSSZ` (with `-<n>` when taken).

| field | holds |
|---|---|
| `schemaVersion`, `id`, `start`, `updated`, `onExisting` | the run |
| `digests` | `config`, `settings` (`perfrepair.yaml`), `screening` |
| `device` | `status` `running`, `done`, `failed` or `stopped`; `step` and `reason` when not done |
| `apps.<app>` | `status` (`running`, `done`, `failed`, `stopped`), `step`, `reason`, `outcome`; `reused` |

| `run.onExisting`, the named record exists | result |
|---|---|
| `overwrite` | every `<app>/finished.json` and `device.yaml` removed: every app and the device benchmark rerun |
| `resume` | the record kept; a done app with its inputs unchanged is reused; the device stage reruns what `device.yaml` does not vouch for |
| `skip` | the stop `run_exists`; nothing runs |

## `primitives.tsv`

One stored, compact view of the benchmark results: on the API 30 emulator run, 4.0 KB for 40 lines against 84.4 KB of `rows.json` and `measurements.json` (100 rows, `timeNs` only).

| part | holds |
|---|---|
| first line | `#schemaVersion<TAB>3`; the reader refuses another |
| key columns | `type`, `algorithm`, `provider`, `operation`, `keySize`, `phase`, `variant`, `status`: one line per key; `type` and `phase` keep two primitives apart that share the rest, `variant` (`fixed`, `notFixed`, schema 3) the two benchmark variants of one primitive, never mixed |
| `status` | the item's run-level `grouping/screen.json` status (no targetSdk); deprecated lines stay with their status, a site's current call needs its own line |
| `<metric>@<input size>` | the median, per registry metric (`dto/metrics.py`) with runs and per input size it was measured at, `@-` without an input size; `-` where that size was not measured |
| `<metric>.n` | the fewest runs among that metric's cells: one energy window beside fifty timings is `energyJ.n` 1, `timeNs.n` 50; schema 1 had one `n`, the fewest over every metric |
| `<metric>.cv` | the largest coefficient of variation among that metric's cells |

- Stored in the registry units (`timeNs` in ns/op), never in the display units: a unit change rewrites no file; a reader converts when it shows a line.
- Numbers carry 4 significant digits: the table is for reading; `measurements.json` keeps the runs, and pImprove is computed from it, never from the table.
- Device stage: rebuilt when `rows.json`, `measurements.json` or `grouping/screen.json` differ from the digests `device.yaml` `primitives` recorded, when inbound or screen rerun, when it is missing or in another schema, and with `guide --refresh`; else reused ([pipeline.md](pipeline.md) Device stage).

## `used.json`

The device items the target apps need, and which app needs each; code joins sites, groups and signatures, no model.

| field | holds |
|---|---|
| `deviceItems` | the count of `grouping/items.json` |
| `apps` | per app folder: `sites` in its `sites.json`, `matched` those whose resolved (type, name, provider) is a device item |
| `items[]` | `{item, via, apps}`: the qualified name, the strongest way any app reaches it, the apps that do |
| `via: site` | an app's site resolves to it |
| `via: group` | a member of the group of a `site` item: its options |
| `via: candidate` | the `site` item has no grouping record yet: every askable item of its family whose signature no component both know sets apart, and the members of their model groups; the model may group them together |

- A site that resolves to no item (`unresolved_*`, `not_on_device`, `name_conflict`, an engine type no family covers) adds nothing.
- Rewritten on each run before the benchmark, and after a screen rerun; absent with `device.filterByApps: false`, so nothing narrows grouping.

## `manifest.yaml` (cryptobenchmark)

| Field | Holds |
|---|---|
| `mode` | `host` or `device` |
| `config` | the global.yaml the run used |
| `deviceId` | the device id derived from the probe's runtime; required on read |
| `runtime` | benchmark.json's runtime; the probe's when nothing was measured |
| `providers[]` | `{name, precedence, serviceCount}` in precedence order |
| `files` | paths relative to the manifest: probe, trial, inventory, effective, prepared, skipped, benchmark, processes[]; a stage that did not run is absent |
| `counts` | prepared, skipped, measured, for the files that exist |
| `units` | `analysis.units`: `latency` (`ms`, `us`, `ns`), `throughput` (`MB/s`, `MiB/s`, `ops/s`); display only; absent before cryptobenchmark recorded it, read as `ms`, `MB/s`; another value fails the read `invalid: manifest units` |

## `run_log.json` statuses

| Status | Means |
|---|---|
| `measured` | a case produced samples |
| `skipped` | preparation or config dropped it (skipped.yaml) |
| `refused` | allowed by the dto; inbound writes none |
| `unmeasured` | prepared, but no samples came back and no file says why (`no_samples`); or in `benchmark.json` without runs of a required metric (`no_required_metric`), left out of the rows |
| `not_runnable` | the inventory marks it `runs: false` (stage `trial`) |
