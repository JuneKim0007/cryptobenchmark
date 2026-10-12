# Artifacts

All in one run directory, except `manifest.yaml` (the benchmark's `results/`).

| Artifact | Producer | Consumers | Validator |
|---|---|---|---|
| `manifest.yaml` | cryptobenchmark `pipeline.py` | inbound | `validation/manifest.py` |
| `rows.json` | inbound | worthiness, validation | `validation/rows.py` |
| `measurements.json` | inbound | worthiness | `validation/measurements.py` |
| `run_log.json` | inbound | — | `validation/run_log.py` |
| `sites.json` | inbound, with `--app` | — | none |
| `grouping/*` | grouping | worthiness reads `groups.json` | `validation/grouping/*`; files: `docs/grouping.md` |
| `worthiness-<mode>/evidence.json` | worthiness | audit | rebuilt from inputs by `validation/run.py` |
| `worthiness-<mode>/outbox/NNNNNN.json` | worthiness | worthiness (resume), validation | the commit; `WorthinessKind.validate` |
| `worthiness-<mode>/verdicts.json` | worthiness | refeed (planned) | `validation/worthiness.py` + projection equality |
| `worthiness-<mode>/journal.jsonl`, `errors.jsonl` | worthiness | audit | — |

- Every JSON document carries `schemaVersion`: 1, except `measurements.json` at 2 (each summary adds `low`, `high`: the median's 95% interval).
- A journal is append-only, one line per model turn, audit only; state is the projection of the outbox.
- `measurements.json` carries the run's `runtime` and `comparability` notes.

## `manifest.yaml` (cryptobenchmark)

| Field | Holds |
|---|---|
| `mode` | `host` or `device` |
| `config` | the global.yaml the run used |
| `runtime` | benchmark.json's runtime; the probe's when nothing was measured |
| `providers[]` | `{name, precedence, serviceCount}` in precedence order |
| `files` | paths relative to the manifest: probe, trial, inventory, effective, prepared, skipped, benchmark, processes[]; a stage that did not run is absent |
| `counts` | prepared, skipped, measured, for the files that exist |

## `run_log.json` statuses

| Status | Means |
|---|---|
| `measured` | a case produced samples |
| `skipped` | preparation or config dropped it (skipped.yaml) |
| `refused` | PlanCheck refused it before any timer |
| `unmeasured` | prepared, but no samples came back and no file says why |
| `not_runnable` | registered, but the trial could not run it |
