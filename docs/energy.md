# Energy

## Capture modes

| `harness.energy.capture` | run | window | operations |
|---|---|---|---|
| `none` (default) | Jetpack timed run only | none | none |
| `measured` | Jetpack timed run, then cooldown | the kept runs: the `Benchmark Time` slice's children from its last `measurement 0` to the last `measurement <n>` after it, whatever heat sleeps lie around them | `repeatIterations` × runs |
| `dry` | `EnergyDryBenchmark`: Cooldown(Rewarm(EnergyWindow(TimedLoop for `windowSeconds`))) | atrace slice `energy:<caseId>` | calls from `energy-dry.yaml` |

- Energy runs only with `--device`; any other capture without it fails.
- `measured`: the window is Jetpack's timed phase; the case's samples (`iterations`, or the energy pass's `samples`) set its length: 100 samples at about 0.11 s is about 11 s, about 110 rail polls; `windowSeconds` does not apply. `dry` is refused with `--harness` and with `run.passes` ([device-session.md](device-session.md#passes)).
- A case's `harness.energy.capture` overrides the run's (`apps/benchmark-runner/energy/capture.py`).
- A `dry` case passed to the timed run fails with `not_timed`; `measured` cases run in `CryptoBenchmark`, `dry` cases in `EnergyDryBenchmark`, one test per case.
- The `energy:<caseId>` marker closes on failure; labels over 127 chars fail with `too_long`.
- Dry calls are appended to `energy-dry.yaml` as `"<id>": <calls>`.

## Config keys

| key | rule | default |
|---|---|---|
| `energy.capture` | `none`, `measured`, `dry` | `none` |
| `energy.windowSeconds` | ≥1; `dry` only | 10 |
| `energy.warmupSeconds` | ≥1 | 2 |
| `energy.cooldownSeconds` | ≥0 | 5 |
| `energy.source` | `rails`, `manafa` | `rails` |

- Keys sit under `harness` in `global.yaml` `run` or a test-set override; precedence: `apps/benchmark/modules/config/docs/config.md`.
- A test-set override sets it per case: `overrides: [{match: {type: Cipher, name: AES/GCM/NoPadding}, set: {harness: {energy: {capture: dry}}}}]`.

## Sources

| `energy.source` | kind | joules from | pre-flight |
|---|---|---|---|
| `rails` (default) | `measured` | Perfetto power rails | below |
| `manafa` | `estimated` | `manafa` 0.4.14: `power_profile.xml`, cpufreq, batterystats | a short session |

- A run has one source; entries that differ fail with `energy_sources_differ`.
- `apps/benchmark-runner/energy_stage.py` picks the adapter; each adapter has `preflight`, `window` (around the device run) and `joules`.
- `manafa` facts, its pre-flight and its reasons: [energy-manafa.md](energy-manafa.md).

## Pre-flight

| step | value |
|---|---|
| windows | idle, then busy (one spin loop per core) |
| window length | 3 s each |
| source | Perfetto `android.power`, rails polled every 100 ms |
| settle | 15 s sleep before the first case, after the plan push and the AOT compile (dex2oat), so the compile heat is not in it |
| output | `discovery/energy.yaml`, traces in `discovery/energy-preflight/` |
| delivery | `energy.yaml` is pushed with the plan |

| `energy.yaml` field | value |
|---|---|
| `schemaVersion` | 1 |
| `railsPresent` | both windows have rails |
| `railsResponsive` | present, idle > 0, busy ≥ 1.10 × idle |
| `idleMicrojoules`, `busyMicrojoules` | window totals |
| `windowSeconds` | pre-flight window length |
| `acceptUnresponsive` | `--energy-accept-unresponsive` |

| refusal (every energy case) | condition |
|---|---|
| `energy_capability_unknown` | no `energy.yaml` in the device directory |
| `no_power_rails` | `railsPresent` false |
| `rails_unresponsive: idle <x> uJ, busy <y> uJ over <s> s` | `railsResponsive` false and not `acceptUnresponsive` |

- On the device the refused cases are left out and listed in `skipped.yaml`; every case refused throws `RefusedPlanException`.
- A case whose `energy.source` is not `rails` reads no rail capability and gets none of these refusals.

## Traces

| capture | source |
|---|---|
| `measured` | Jetpack per-case Perfetto traces, pulled from the androidx media directory |
| `dry` | host Perfetto session around `EnergyDryBenchmark` from `apps/benchmark-runner/energy/energy.pbtx` |

- `energy.pbtx`: 16384 KB ring buffer, power rails every 100 ms, `atrace_apps io.github.junekim0007.cryptobench`, `process_stats`, `write_into_file` every 2500 ms, max 3600000 ms.
- Traces are pulled after every case (`traces: <case>: <n> pulled`): with one process per case, the device keeps only the latest case's trace, so a pull at the process's end would find one (seen on a Pixel 10: 41 of 42 cases `trace_not_pulled`). Large traces: Jetpack's own trace config, fixed in androidx 1.5.0, records memory counters; an allocating call floods it (seen: AES/GCM encrypt traces of 38 to 125 MB, 5.66M `mem.rss.anon` samples, rails lost as `window_uncovered`). Chosen: keep `measured` (`dry` is refused with `--harness` and with `run.passes`) and shorten the window with the energy pass's `samples` (100, a third of a 300-sample trace); a case above 32 MiB is flagged `traceLarge`, a lost window is `window_uncovered` with no number, never a wrong one; `traces:    <case>: <n> on the device` per case settles a missing trace. Every cipher call now includes `init`, so CBC and CTR allocate per call as GCM did; whether 100 samples keep their traces whole only a phone shows.
- Rails are counter tracks named `power.%`, cumulative µJ; window edges are interpolated linearly; a window outside the samples is `window_uncovered`, one that ends before it starts `empty_window`.
- `measured` windows shift by BOOTTIME − MONOTONIC, taken from the first clock snapshot holding both (a Pixel 10 trace can open with BOOTTIME alone); exactly one timed phase per case is required.

## Outputs

`benchmark/energy.json`: top level `schemaVersion` 2, `source`, `kind` (`measured` for rails, `estimated` for manafa), `cases`; rails adds `railsResponsive`, manafa adds `powerProfile`.

| case field | value |
|---|---|
| `joules` | gross energy over the window |
| `netJoules` | gross − idle rate × window |
| `operations` | see capture modes |
| `joulesPerOperation` | net / operations |
| `windowSeconds`, `polls`, `shortWindow`, `rails`, `capture`, `clockOffsetNs` | window facts |
| `heatSleepAfterKeptRuns` | `measured`: Jetpack slept for heat after the kept runs began; it keeps such runs once its sleeps are spent, so they may be hot; printed `flagged:` |
| `traceBytes`, `traceLarge` | `measured`: the trace's size; large above 32 MiB, where rail samples were lost before; printed `flagged:` |
| `valid`, `invalid` | judgement and reasons |

| invalid reason | condition |
|---|---|
| `rails_unresponsive` | rails not responsive |
| `window_uncovered` | the timed phase reaches past the first or last rail sample; the case has no number, the run goes on |
| `short_window` | < 20 polls |
| `net_not_positive` | `netJoules` ≤ 0 |
| `no_operations` | `operations` is 0 or absent |
| `no_joules_per_operation` | no other reason, yet `joulesPerOperation` is null; a valid case always has a number |
| `trace_not_pulled` | `measured`: the case's Jetpack trace is not in `traces/` |
| `trace_unreadable: <error>` | `measured`: the trace processor failed on the case's trace |
| `timed_phases: <n>` | `measured`: not exactly one timed phase |
| `no_measurement_slices` | `measured`: the timed phase has no `measurement 0` child |
| `no_clock_snapshot` | `measured`: no BOOTTIME/MONOTONIC snapshot in the trace |
| `no_call_count` | `dry`: a marker without its line in `energy-dry.yaml` |
| `no_rails` | the trace has no `power.%` counter |
| `empty_window` | the window ends before it starts |
| `not_measured: <reason>` | manafa gave no number: [energy-manafa.md](energy-manafa.md#not-measured); the case-level reasons above reach manafa the same way |

- A case without a window keeps `operations` and holds its reason in `notMeasured`; `joules`, `joulesPerOperation`, `windowSeconds` are null, `clockOffsetNs` is null when no trace was read.
- One case's problem is that case's reason; `energy.py` exits 0 and writes every other case.
- An energy step that fails as a whole (the source's window around a timed process, trace pull, dry pass beside a timed run, `energy.py` or manafa's answer) prints `error: energy_failed: <message>`, adds the line to `manifest.yaml` `problems`, and leaves no `energy.json` for that process; `ConvertKt` still writes the timing.
- `ConvertKt` joins valid `measured` cases into `benchmark.json` as `energyJ` (runs = [`joulesPerOperation`], iterations = `operations`, `source`, `kind`).
- `MergeRunsKt` carries `source` and `kind`; processes with different ones fail with `energy_kinds_differ` or `energy_sources_differ`.
- An `energy.json` of another `schemaVersion` is `unsupported` and joins nothing.
- An estimated run: `manifest.yaml` top-level `energy`, a closing line in `analysis/summary.md`, `(estimated)` on its `energyJ` chart.
- Other `measured` cases print `energy_not_joined: <id>: <reasons>` (`unjudged` when no reason; `missing_field: joulesPerOperation`, `out_of_range: operations <n>` for a valid case without a usable number).
- An `energy.json` `ConvertKt` cannot read prints `energy_not_joined: <file>: <message>`; the timing converts without energy.

## Files

```
apps/benchmark-runner/energy_session.py : starts, stops and pulls Perfetto sessions on the device
apps/benchmark-runner/energy_stage.py : capture selection, the run's one source
apps/benchmark-runner/energy/capture.py : resolves a node's capture and source against the default
apps/benchmark-runner/energy/energy.pbtx : Perfetto config for the dry host session
apps/benchmark-runner/energy/energy.py : rail traces to energy.json; the case windows both sources read
apps/benchmark-runner/energy/manafa_estimate.py : joules per case window from a stopped EManafa, or not_measured
apps/benchmark-runner/energy/manafa_session.py : the process holding one EManafa; the manafa pre-flight check
apps/benchmark-runner/energy/preflight.py : idle and busy traces to energy.yaml
apps/benchmark-runner/energy/rails/ : cumulative counter arithmetic; trace queries for rails, markers, timed phases, clock offset
apps/benchmark-runner/energy/requirements-manafa.txt : manafa, pinned; optional
apps/benchmark-runner/energy/requirements.txt : perfetto, pyyaml
apps/benchmark-runner/energy/sources/ : one adapter per energy.source on the host; how the host runs apps/benchmark-runner/energy
apps/benchmark-runner/energy/tests/ : capture, counters, window, preflight, judge and source tests; a fake manafa; recorded rails output
```

| command | arguments |
|---|---|
| `preflight.py` | `<idle.pftrace> <busy.pftrace> <window seconds> <out energy.yaml> [--accept-unresponsive]` |
| `energy.py` | `--capability F -o OUT [--prepared --benchmark-data --traces] [--dry-trace --dry-calls]` |
| `manafa_session.py` | `[--check <seconds> --capability <energy.yaml>]`; without them, stdin `stop`, then a JSON list of `energy.py`'s arguments |

- Missing `perfetto` fails with an error naming `pip install -r apps/benchmark-runner/energy/requirements.txt` and `--energy-python`.
