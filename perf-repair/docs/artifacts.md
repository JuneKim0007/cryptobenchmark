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
| `manifest.yaml` | cryptobenchmark `pipeline.py` | inbound, grouping build, probe_device (`inputs`) | `validation/manifest.py` |
| `device.yaml` | probe_device, last | probe_device | `DeviceRecord.from_json`: schema, the four input digests, the manifest's sha256; unreadable counts as absent |
| `rows.json` | inbound | worthiness, validation | `validation/rows.py` |
| `measurements.json` | inbound | worthiness, validation | `validation/measurements.py` |
| `run_log.json` | inbound | validation | `validation/run_log.py` |
| `<app>/sites.json` | `perfrepair.app` | scope | none |
| `<app>/app.json` | `perfrepair.app` | dossier | `validation/app.py`, before writing |
| `<app>/gaps.json` | `perfrepair.app` | `check/run.py` | `validation/gaps.py`, before writing: closed lists, unique ids, cited lines in the file, each gap an open requirement of its scope |
| `<app>/scopes.json` | `perfrepair.app` | dossier, harness | `validation/app.py`, before writing: schema 3, every scope's lifecycle in its closed lists, cited lines inside the file |
| `grouping/*` | grouping | worthiness and repair read `groups.json` | `validation/grouping/*`; files: `docs/grouping.md` |
| `worthiness-<mode>/evidence.json` | worthiness | audit | none |
| `worthiness-<mode>/outbox/<fingerprint>/NNNNNN.json`, `outbox/active` | worthiness | worthiness (resume), validation | the commit; `WorthinessKind.validate` |
| `<app>/finished.json` | the guide, when an app reaches its last step | the guide's targets loop | digests compared, no validator: a mismatch only runs the app |
| `*/outbox/<fingerprint>/charter.json` | the engine, when it opens the outbox | the engine (`charter_mismatch`), validation | `check/run.py`: rehashed to the folder's name |
| `grouping/supervisor.charter.json` | grouping report --supervisor | validation | `check/run.py`: rehashed to `supervisor.json` `charter` |
| `log/events.jsonl` | every command, appended | watch, log summary, the views | `validation/events.py` |
| `log/screening/ai.log`, `log/grouping/ai.log`, `log/bug.log` | the event sink, from the same events | people | none: `log/views.py` renders them |
| `worthiness-<mode>/verdicts.json` | worthiness | validation | `validation/verdicts.py` + projection equality |
| `worthiness-<mode>/journal.jsonl`, `errors.jsonl` | worthiness | audit | none |
| `<app>/dossiers.json` | repair dossier | replace, repair test-set | `validation/dossiers.py`, before writing |
| `<app>/edits.json`, `original/`, `patched/` | repair edit | repair harness | `validation/repair.py`, before writing |
| `<app>/harness.yaml`, `harness/<scope>/` | repair harness | cryptobenchmark | `validation/repair.py`, before writing |
| `<app>/measured/` | cryptobenchmark `pipeline.py --device --harness` | report | cryptobenchmark |
| `<app>/report.json`, `report.md` | report app | report summary | `validation/report.py`, before writing |
| `summary.json`, `summary.md` | report summary | people | `validation/report.py`, before writing |
| test-set YAML (`-o`) | repair test-set | cryptobenchmark | none |

- Every JSON document carries `schemaVersion`: 1, except `measurements.json` at 3 (each summary adds `low`, `high`: the median's 95% bootstrap interval, `null` below 2 runs; and `processes`: its runs per process).
- A journal is append-only, one line per model turn with its `durationMs`, audit only; state is the projection of the outbox.
- `charter.json` holds the system and correction texts, the schema, the inputs and each prompt's `source` (`packaged` or the override path); an outbox from before it gets it on its next open.
- `measurements.json` carries the run's `runtime` and `comparability` notes; a case with `energyJ` runs has an `energyJ` summary with its `kind`.
- `check/run.py` rebuilds evidence from rows, measurements and `groups.json` to check verdicts.

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

## `run_log.json` statuses

| Status | Means |
|---|---|
| `measured` | a case produced samples |
| `skipped` | preparation or config dropped it (skipped.yaml) |
| `refused` | allowed by the dto; inbound writes none |
| `unmeasured` | prepared, but no samples came back and no file says why |
| `not_runnable` | the inventory marks it `runs: false` (stage `trial`) |
