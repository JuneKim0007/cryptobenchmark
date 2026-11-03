# Energy

## Capture modes

| `harness.energy.capture` | run | window | operations |
|---|---|---|---|
| `none` (default) | Jetpack timed run only | none | none |
| `measured` | Jetpack timed run, then cooldown | Jetpack `Benchmark Time` slice, from the end of its last `Sleep due to Thermal Throttle` child | `repeatIterations` × runs |
| `dry` | `EnergyDryBenchmark`: Cooldown(Rewarm(EnergyWindow(TimedLoop for `windowSeconds`))) | atrace slice `energy:<caseId>` | calls from `energy-dry.yaml` |

- Energy runs only with `--device`; any other capture without it fails.
- A case's `harness.energy.capture` overrides the run's (`tools/energy/capture.py`).
- A `dry` case passed to the timed run fails with `not_timed`.
- `measured` cases run in `CryptoBenchmark`; `dry` cases run in `EnergyDryBenchmark`, one parameterised test per case.
- The `energy:<caseId>` marker closes on failure; labels over 127 chars fail with `too_long`.
- Dry calls are appended to `energy-dry.yaml` as `"<id>": <calls>`.

## Config keys

| key | rule | default |
|---|---|---|
| `energy.capture` | `none`, `measured`, `dry` | `none` |
| `energy.windowSeconds` | ≥1 | 10 |
| `energy.warmupSeconds` | ≥1 | 2 |
| `energy.cooldownSeconds` | ≥0 | 5 |
| `energy.source` | `rails`, `manafa` | `rails` |

- Keys sit under `harness` in `global.yaml` `run` or a test-set override; precedence: `modules/config/docs/config.md`.
- `config/global-energy.yaml`: `capture: measured`, windows 3/1/1 s, test set `testsets/energy-smoke.yaml`.
- `config/testsets/energy-smoke.yaml`: SHA-256, HmacSHA256 measured; AES/GCM/NoPadding `dry`.

## Sources

| `energy.source` | kind | joules from | pre-flight |
|---|---|---|---|
| `rails` (default) | `measured` | Perfetto power rails | below |
| `manafa` | `estimated` | `manafa` 0.4.14: `power_profile.xml`, cpufreq, batterystats | a short session |

- A run has one source; entries that differ fail with `energy_sources_differ`.
- `scripts/energy_stage.py` picks the adapter; each adapter has `preflight`, `window` (around the device run) and `joules`.
- `manafa` facts, its pre-flight and its reasons: [energy-manafa.md](energy-manafa.md).

## Pre-flight

| step | value |
|---|---|
| windows | idle, then busy (one spin loop per core) |
| window length | 3 s each |
| source | Perfetto `android.power`, rails polled every 100 ms |
| settle | 15 s sleep before the first case |
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

- Any refusal throws `RefusedPlanException` on the device.
- A case whose `energy.source` is not `rails` reads no rail capability and gets none of these refusals.

## Traces

| capture | source |
|---|---|
| `measured` | Jetpack per-case Perfetto traces, pulled from the androidx media directory |
| `dry` | host Perfetto session around `EnergyDryBenchmark` from `tools/energy/energy.pbtx` |

- `energy.pbtx`: 16384 KB ring buffer, power rails every 100 ms, `atrace_apps io.github.junekim0007.cryptobench`, `process_stats`, `write_into_file` every 2500 ms, max 3600000 ms.
- Rails are counter tracks named `power.%`; counters are cumulative µJ.
- Window edges are interpolated linearly; a window outside the samples raises `uncovered`.
- `measured` windows shift by BOOTTIME − MONOTONIC; exactly one timed phase per case is required.

## Outputs

`benchmark/energy.json`: top level `schemaVersion` 2, `source`, `kind` (`measured` for rails, `estimated` for manafa), `cases`; rails adds `railsResponsive`, manafa adds `powerProfile`.

| case field | value |
|---|---|
| `joules` | gross energy over the window |
| `netJoules` | gross − idle rate × window |
| `operations` | see capture modes |
| `joulesPerOperation` | net / operations |
| `windowSeconds`, `polls`, `shortWindow`, `rails`, `capture`, `clockOffsetNs` | window facts |
| `valid`, `invalid` | judgement and reasons |

| invalid reason | condition |
|---|---|
| `rails_unresponsive` | rails not responsive |
| `short_window` | < 20 polls |
| `net_not_positive` | `netJoules` ≤ 0 |
| `not_measured: <reason>` | manafa gave no number: [energy-manafa.md](energy-manafa.md#not-measured) |

- `ConvertKt` joins valid `measured` cases into `benchmark.json` as `energyJ` (runs = [`joulesPerOperation`], iterations = `operations`, `source`, `kind`).
- `MergeRunsKt` carries `source` and `kind`; processes with different ones fail with `energy_kinds_differ` or `energy_sources_differ`.
- An `energy.json` of another `schemaVersion` fails with `unsupported`.
- An estimated run: `manifest.yaml` top-level `energy`, a closing line in `analysis/summary.md`, `(estimated)` on its `energyJ` chart.
- Other `measured` cases print `energy_not_joined: <id>: <reasons>` (`unjudged` when no reason).

## Files

```
scripts/energy_session.py : starts, stops and pulls Perfetto sessions on the device
scripts/energy_stage.py : capture selection, the run's one source
tools/energy/capture.py : resolves a node's capture and source against the default
tools/energy/energy.pbtx : Perfetto config for the dry host session
tools/energy/energy.py : rail traces to energy.json; the case windows both sources read
tools/energy/manafa_estimate.py : joules per case window from a stopped EManafa, or not_measured
tools/energy/manafa_session.py : the process holding one EManafa; the manafa pre-flight check
tools/energy/preflight.py : idle and busy traces to energy.yaml
tools/energy/rails/ : cumulative counter arithmetic; trace queries for rails, markers, timed phases, clock offset
tools/energy/requirements-manafa.txt : manafa, pinned; optional
tools/energy/requirements.txt : perfetto, pyyaml
tools/energy/sources/ : one adapter per energy.source on the host; how the host runs tools/energy
tools/energy/tests/ : capture, counters, window, preflight, judge and source tests; a fake manafa; recorded rails output
```

| command | arguments |
|---|---|
| `preflight.py` | `<idle.pftrace> <busy.pftrace> <window seconds> <out energy.yaml> [--accept-unresponsive]` |
| `energy.py` | `--capability F -o OUT [--prepared --benchmark-data --traces] [--dry-trace --dry-calls]` |
| `manafa_session.py` | `[--check <seconds> --capability <energy.yaml>]`; without them, stdin `stop`, then a JSON list of `energy.py`'s arguments |

- Missing `perfetto` fails with an error naming `pip install -r tools/energy/requirements.txt` and `--energy-python`.
