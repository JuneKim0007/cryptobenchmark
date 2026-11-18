# Validation

## Case rules

Every pulled `cases/<id>.json` is held against one rules table (`lib/cryptobench/cryptobench/stages/measurement/validation/rules.py`), in order, up to the first `fail`; the expectation is the run record's run block (`validation/expectation.py`), never the live config.

| code | severity | condition |
|---|---|---|
| `no_data` | fail | no `benchmarkData.json` after a passing launch |
| `result_mismatch` | fail | `benchmarks[0].name`, without the error ids androidx prefixes (`EMULATOR_`), is not `measure[<id>]` (another case's result, none, unreadable) |
| `miscalibrated` | fail | a sample under 1 ms: androidx's calls per sample collapsed after a stalled warm-up |
| `sample_count` | fail | `timeNs.runs` is not the samples the pass asked for (a relaunch's own count; the single pass: the case's `harness.iterations` in `prepared.yaml`, unchecked when none) |
| `warmup_near_cap` | note | the warm-up probably ended at androidx's 8 s limit instead of settling; printed `note: warmup_near_cap: ...` |

- A fail: the attempt's file moves to `rejected/<UTC>/[<pass>/]process-<n>/<id>.json` beside `why.yaml` (`schemaVersion`, `case`, `run`, `attempt`, `findings`), the line is `case_failed: <id>: <code>: <detail>`, and the case is retried as a failed launch (`launchRetries`); the main tree holds only files that passed.
- Every launch again is one `{case, attempt, code}` in the process's `relaunched` of its block record: a fail's code, a failed launch's code (`case_failed` when it carries none), `device_lost`, `temperature_discarded`, `short_window`.
