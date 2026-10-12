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

- Every JSON document carries `schemaVersion: 1`.
- A journal is append-only, one line per model turn, audit only; state is the projection of the outbox.
- `measurements.json` carries the run's `runtime` and `comparability` notes.
