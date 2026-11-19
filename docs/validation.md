# Validation

## Case rules

Every pulled `cases/<id>.json` is held against one rules table (`lib/cryptobench/cryptobench/stages/measurement/validation/rules.py`), in order, up to the first `fail`; the expectation is the run record's run block (`validation/expectation.py`), never the live config.

| code | severity | condition |
|---|---|---|
| `no_data` | fail | no `benchmarkData.json` after a passing launch |
| `result_mismatch` | fail | `benchmarks[0].name`, without the error ids androidx prefixes (`EMULATOR_`), is not `measure[<id>]` (another case's result, none, unreadable) |
| `miscalibrated` | fail | a sample under 1 ms: androidx's calls per sample collapsed after a stalled warm-up |
| `sample_count` | fail | `timeNs.runs` is not the samples the pass asked for (a relaunch's own count; the single pass: the case's `harness.iterations` in `prepared.yaml`, unchecked when none) |
| `warmup_near_cap` | note | `warmupIterations` × the median sample ≥ 6 s (`WARMUP_NEAR_CAP_S`): the warm-up probably ended at androidx's 8 s limit instead of settling; printed `note: warmup_near_cap: ...` |

- A fail: the attempt's file moves to `rejected/<UTC>/[<pass>/]process-<n>/<id>.json` beside `why.yaml` (`schemaVersion`, `case`, `run`, `attempt`, `findings`), the line is `case_failed: <id>: <code>: <detail>`, and the case is retried as a failed launch (`launchRetries`); the main tree holds only files that passed.
- Every launch again is one `{case, attempt, code}` in the process's `relaunched` of its block record: a fail's code, a failed launch's code (`case_failed` when it carries none), `device_lost`, `temperature_discarded`, `short_window`.
- An attempt that ends hot (`temperature_discarded`) or unreadable (`temperature_unreadable`), or loses the device (`device_lost`), moves to `rejected/` the same way, its `why.yaml` holding one finding with that code; `why.yaml` alone when no file was pulled.

## Run rules

`check_run` holds one run (a process folder) against `check_case` for every case it kept a file of, then the run rows; the single pass's expected samples come from `preparation/prepared.yaml` once the process pulled it. A host run keeps no per-case files: its `order.txt` has no `cases/` beside it, so only `files_differ` applies.

| code | severity | condition |
|---|---|---|
| `case_missing` | fail | a case of `order.txt` with no `cases/<id>.json` and no `case_failed: <id>:` or `case_skipped: <id>:` line of the run |
| `case_extra` | note | a `cases/*.json` the run did not launch |
| `files_differ` | fail | a file missing, added or changed against the block record's `files`; the case named when the file is `cases/<id>.json` |
| `short_window` | note | energy pass only: `energy-samples.yaml` flags the case `shortWindow` (kept below `minWindowSeconds`) |
| `window_uncovered` | note | energy pass only: `energy.json` gives the case `window_uncovered` among its `invalid` reasons |

| when | what runs | on a fail |
|---|---|---|
| a process's end, its plan pulled, its hooks still open | `check_run` without a record | each case a fail names moves to `rejected/` and is launched once more in the process (one `relaunched` entry, its code the fail's; printed `case:      <id> launched again (<code>) ok`), then `benchmarkData.json` is merged again |
| a block's end, before its record and the next run | `check_run` per run of the block | recorded only: the record's `processes[].findings` and `validation.yaml` |

## validation.yaml

In the device folder, part of the unit (a publish moves it aside with `manifest.yaml`): `schemaVersion: 1`, `runs: {<run>: {checkedBy, fails, findings}}`, `<run>` the process folder under `benchmark/` (`process-<n>`, `<pass>/process-<n>`); each check replaces its runs' entries. `checkedBy`: `block_end` or `restart`. A finding: `code`, `scope` (`case`, `run`), `run`, `case`, `detail`, `severity` (`fail`, `note`).

## Audit

`pipeline.py --audit RESULTS` (`lib/cryptobench/cryptobench/stages/measurement/validation/audit.py`) reads, never changes: every unit under `RESULTS` holding `manifest.yaml` and `benchmark/`, outside `superseded/` and `rejected/`, through its block records (`schemaVersion` 3 only) and `check_run`.

`RESULTS/audit.yaml`: `schemaVersion: 1`, `units: {<unit>: {<pass or single>: {runs, cases: {<id>: {runsPresent, relaunched, rejected, findings {code: runs}, outliers}}}}}`; `outliers`: the runs whose median of `timeNs.runs` is outside Tukey's fences (1.5 × IQR) over the case's runs, from 4 runs on; flagged only.
