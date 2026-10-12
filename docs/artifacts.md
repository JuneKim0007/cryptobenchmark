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
| `evidence-<mode>.json` | worthiness | audit | rebuilt from inputs by `validation/verdicts.py` |
| `worthiness-<mode>.state.json` | worthiness | refeed (planned) | `validation/verdicts.py` |
| `worthiness-<mode>.journal.jsonl` | worthiness | validation (replay) | `validation/replay.py` |
| `worthiness-<mode>.queue.json` | worthiness | worthiness (resume) | queue open: same items or refuse |

- Every JSON document carries `schemaVersion: 1`.
- A journal is append-only; one line per model call.
- `measurements.json` carries the run's `runtime` and `comparability` notes.
