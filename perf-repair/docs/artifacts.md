# Artifacts

- One run directory holds every artifact, except `manifest.yaml` (the benchmark's `results/`) and the `repair test-set` YAML (its `-o` path).

| Artifact | Producer | Consumers | Validator |
|---|---|---|---|
| `manifest.yaml` | cryptobenchmark `pipeline.py` | inbound, grouping build | `validation/manifest.py` |
| `rows.json` | inbound | worthiness, validation | `validation/rows.py` |
| `measurements.json` | inbound | worthiness, validation | `validation/measurements.py` |
| `run_log.json` | inbound | validation | `validation/run_log.py` |
| `sites.json` | inbound, with `--app` | repair candidates (`--sites`) | none |
| `grouping/*` | grouping | worthiness and repair read `groups.json` | `validation/grouping/*`; files: `docs/grouping.md` |
| `worthiness-<mode>/evidence.json` | worthiness | audit | none |
| `worthiness-<mode>/outbox/<fingerprint>/NNNNNN.json`, `outbox/active` | worthiness | worthiness (resume), validation | the commit; `WorthinessKind.validate` |
| `worthiness-<mode>/verdicts.json` | worthiness | repair choose | `validation/worthiness.py` + projection equality |
| `worthiness-<mode>/journal.jsonl`, `errors.jsonl` | worthiness | audit | none |
| `apps/<app>/dossiers.json` | `result dossier` | replace | `validation/dossiers.py` |
| `repair/<app>/candidates.json` | repair candidates | repair test-set, choose | none |
| `repair/<app>/choices.json` | repair choose | repair patch | none |
| `repair/<app>/patches.json` | repair patch | none | `validation/repair.py`, before writing |
| test-set YAML (`-o`) | repair test-set | cryptobenchmark | none |

- Every JSON document carries `schemaVersion`: 1, except `measurements.json` at 3 (each summary adds `low`, `high`: the median's 95% bootstrap interval, `null` below 2 runs; and `processes`: its runs per process).
- A journal is append-only, one line per model turn, audit only; state is the projection of the outbox.
- `measurements.json` carries the run's `runtime` and `comparability` notes.
- `validation/run.py` rebuilds evidence from rows, measurements and `groups.json` to check verdicts.

## `manifest.yaml` (cryptobenchmark)

| Field | Holds |
|---|---|
| `mode` | `host` or `device` |
| `config` | the global.yaml the run used |
| `runtime` | benchmark.json's runtime; the probe's when nothing was measured |
| `providers[]` | `{name, precedence, serviceCount}` in precedence order |
| `files` | paths relative to the manifest: probe, trial, inventory, effective, prepared, skipped, benchmark, processes[]; a stage that did not run is absent; perf-repair reads all but `effective` |
| `counts` | prepared, skipped, measured, for the files that exist |

## `run_log.json` statuses

| Status | Means |
|---|---|
| `measured` | a case produced samples |
| `skipped` | preparation or config dropped it (skipped.yaml) |
| `refused` | allowed by the dto; inbound writes none |
| `unmeasured` | prepared, but no samples came back and no file says why |
| `not_runnable` | the inventory marks it `runs: false` (stage `trial`) |
