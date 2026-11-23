# Energy

## Capture modes

| `harness.energy.capture` | run | window | operations |
|---|---|---|---|
| `none` (default) | Jetpack timed run only | none | none |
| `measured` | Jetpack timed run of the energy pass (`run.passes.energy`); its rest is the host's: the thermal gate and `caseCooldownSeconds` | the kept runs: the `Benchmark Time` slice's children from its last `measurement 0` to the last `measurement <n>` after it, whatever heat sleeps lie around them | `repeatIterations` × runs |
| `dry` | `EnergyDryBenchmark`: Cooldown(Rewarm(EnergyWindow(TimedLoop for `windowSeconds`))) | atrace slice `energy:<caseId>` | calls from `energy-dry.yaml` |

- Energy runs only with `--device`; any other capture without it fails.
- `measured`: needs `run.passes.energy`; without `run.passes` it is refused (`not_supported`), and the other passes run every case with capture `none`. The window is Jetpack's timed phase; the energy pass's `samples` set its length; `windowSeconds` does not apply. After each passing energy launch the host estimates the window as `repeatIterations` × Σ `timeNs.runs` of the pulled file. A case is sized once per run (`lib/cryptobench/cryptobench/stages/measurement/session/window.py`): in the first process that measures it, a window below `run.passes.energy.minWindowSeconds` (default 5) is launched once more with ⌈samples × 1.5 × minimum / window⌉ samples, its pulled file replaced, outside `launchRetries`; the count it keeps (the relaunch's, else the pass's) is the count every later process launches it with, never relaunched; still short, or a relaunch that fails every retry, is one `short_window` warning and the case keeps its last short result. A process that gives the case up decides nothing. A resumed run takes the counts from its kept processes' `energy-samples.yaml`. Each process writes `energy-samples.yaml`: `minWindowSeconds` and per case `samples` (its first launch's count), `windowSeconds`, `relaunched {samples, windowSeconds}`, `shortWindow`. `dry` is refused with `run.passes` (`not_supported`, [device-session.md](device-session.md#passes)).
- A case's `harness.energy.capture` overrides the run's (`apps/benchmark-runner/energy/capture.py`; the runner reads the same rule from `lib/cryptobench/cryptobench/shared/settings/energy_capture.py`); their defaults equal `lib/cryptobench/cryptobench/shared/settings/defaults.yaml` (`test_defaults.py`).
- A `dry` case passed to the timed run fails with `not_timed`; `measured` cases run in `CryptoBenchmark`, `dry` cases in `EnergyDryBenchmark`, one test per case. A `dry` case preparation skipped under `onFailure: continue` is a JUnit assumption failure, so the dry pass still passes; the host prints `case_skipped: <id>: <code>` for each one `skipped.yaml` holds with a final code, and a dry-only run whose every dry case is one is `all_cases_skipped`; `EnergyDryBenchmark` writes `energy-dry.yaml` empty before its first case, so the host always pulls it.
- The `energy:<caseId>` marker closes on failure; labels over 127 chars fail with `too_long`. Dry calls are appended to `energy-dry.yaml` as `"<id>": <calls>`. A case's `afterCall` (a `secure` case deleting its key) runs after each call inside either window, so its energy counts in the case's.

## Config keys

| key | rule | default |
|---|---|---|
| `energy.capture` | `none`, `measured`, `dry` | `none` |
| `energy.windowSeconds` | ≥1; `dry` only | 10 |
| `energy.warmupSeconds` | ≥1 | 2 |
| `energy.cooldownSeconds` | ≥0; `dry` only (its cases share one process and one gate hold); set on a `measured` capture it is a `shadowed_setting` warning | 5 |
| `energy.source` | `rails`, `manafa` | `rails` |

- Keys sit under `harness` in `global.yaml` `run` or a test-set override; precedence: `apps/benchmark/modules/config/docs/config.md`. Defaults: `EnergySettings.DEFAULTS`, written to `lib/cryptobench/cryptobench/shared/settings/defaults.yaml`; `Energy.of` merges a case's keys over them key by key.
- A test-set override sets it per case: `overrides: [{match: {type: Cipher, name: AES/GCM/NoPadding}, set: {harness: {energy: {capture: dry}}}}]`.

## Sources

| `energy.source` | kind | joules from | pre-flight |
|---|---|---|---|
| `rails` (default) | `measured` | Perfetto power rails | below |
| `manafa` | `estimated` | `manafa` 0.4.14: `power_profile.xml`, cpufreq, batterystats | an idle session of `run.energyIdleSeconds` |

- A run has one source; entries that differ fail with `energy_sources_differ`. Each adapter's `CAPTURES` lists the captures it measures (`rails`: `measured`, `dry`; `manafa`: `dry`); any other capture in the run stops it with `not_supported: energy.source <source> captures <captures>; it measures <captures>` before any device step.
- `lib/cryptobench/cryptobench/stages/measurement/energy/steps.py` picks the adapter; each adapter has `preflight`, `idle_end`, `window` (around the device run) and `joules`.
- `manafa` facts, its pre-flight and its reasons: [energy-manafa.md](energy-manafa.md).

## Pre-flight

| step | value |
|---|---|
| windows | after the plan push and the AOT compile (dex2oat): idle `run.energyIdleSeconds` (default 120, [config.md](../apps/benchmark/modules/config/docs/config.md)), then busy 3 s (`BUSY_SECONDS` in `lib/cryptobench/cryptobench/stages/measurement/energy/sources/rails_source.py`, one spin loop per core); rails: after the last pass, idle again (`idle-end.pftrace`); manafa subtracts no idle and takes no end reading |
| source | Perfetto `android.power`, rails polled every 100 ms, 4096 KB buffer (`RAILS_CONFIG`) |
| heat | each idle reading (start and end) first holds behind the energy pass's thermal gate (`run.passes.energy.thermalGate` when :config wrote one, else `run.thermalGate`; its session `energy idle`; no other wait); no sleep after the busy window ([device-session.md](device-session.md#thermal-gate)) |
| output | `discovery/energy.yaml`, traces in `discovery/energy-preflight/`; `energy.yaml` is pushed with the plan |

| `energy.yaml` field | value |
|---|---|
| `schemaVersion` | 4 (`CAPABILITY_VERSION` in `apps/benchmark-runner/energy/energy.py`); another is `unsupported_schema_version` in `energy.py` and `EnergyCapability` |
| `railsPresent` | both windows have rails |
| `railsResponsive` | present, idle > 0, busy power ≥ 1.10 × idle power in µJ/s (`RESPONSIVE` in `apps/benchmark-runner/energy/preflight.py`) |
| `idleMicrojoules`, `busyMicrojoules`; `idle`/`busy`/`idleEnd` `ExcludedMicrojoules`; `idleWindowSeconds`, `busyWindowSeconds`; `railSubsystems` | window totals over the summed rails; the excluded rails' totals (printed on the `rails:` line); configured lengths; the busy trace's `{raw_name: subsystem_name or null}`, once per run, printed on the `rails:` line as `summed subsystems <names> vs excluded <names>` |
| `idleSpanSeconds`, `idleMicrowatts` | the span the idle trace's rail samples cover; idle power = `idleMicrojoules` / that span (0 without one); a span under 90% of `idleWindowSeconds` adds `idle_span_short: <reading>: rail samples span <s> of <t> s; idle power is over the span` to `problems` |
| `idleSkin`, `idleEndSkin` | `{start, end}`: the skin temperature (`{sensor, celsius}`, null unread) when the idle reading began and ended; printed on the `rails:` and `idle:` lines (`skin <c> C -> <c> C (<sensor>)`) |
| `idleBoottimeNs`; `idleEnd{Microjoules,WindowSeconds,SpanSeconds,Microwatts,BoottimeNs}` | BOOTTIME midpoint of the start trace's rail samples (null without rails); the end reading, added by `preflight.py --end` |
| `idleDriftPercent` | (`idleEndMicrowatts` − `idleMicrowatts`) / `idleMicrowatts` × 100; printed `idle:      start <w> W, end <w> W, <h> h apart, drift <±p>%; end <s> of <t> s, skin …` |
| `acceptUnresponsive` | `--energy-accept-unresponsive` |

| refusal (every energy case) | condition |
|---|---|
| `energy_capability_unknown` | no `energy.yaml` in the device directory |
| `no_power_rails` | `railsPresent` false |
| `rails_unresponsive: idle <x> uJ over <s> s, busy <y> uJ over <t> s` | `railsResponsive` false and not `acceptUnresponsive` |

- The refused cases are left out and listed in `skipped.yaml`, on the host and the device; every case refused throws `RefusedPlanException` after `skipped.yaml` holds each refusal and `prepared.yaml` no case, and a run of only final refusals ends `all_cases_skipped` ([device-session.md](device-session.md#thermal-gate)). A case whose `energy.source` is not `rails` reads no rail capability and gets none of these refusals.
- Idle baseline: every `measured` and `dry` window subtracts the idle power on the BOOTTIME line between `idleMicrowatts` and `idleEndMicrowatts`, at the window's midpoint, × its length. A run with no energy capture, and a `--bench` run, take no reading.
- Each process's `energy.json` is first written from the start reading alone (`idleBaseline: idle_start_only`); after the end reading `energy.py` and `ConvertKt` run again for every process this run measured (`idle:      energy again for <n> processes …`), each into the process's `energy-redo/`; only once every process succeeded are the staged `energy.json` and `benchmark.json` moved over the old ones (now `interpolated`), their block records' `files` digests rewritten and the merges run again. `energy-redo/` is removed either way. Any process failing its redo leaves every process as the start reading wrote it (`energy_failed: energy again: <message>`, `idle_start_only: energy again failed; …`): a run never mixes the two baselines. A resumed run interpolates only the processes it measured: a kept block's processes keep their `energy.json` (its energy and the idle it subtracted, from the run that measured them, `idle_start_only` for a run that stopped). A kept run that captured energy and fails a check is measured again whole, never by case, so no earlier trace meets this run's idle line ([results.md](results.md#resuming-a-stopped-run)).
- No end reading (the run stopped first; any failure before or during it, a lost device (`DeviceLost` waited out to `DeviceGone`) and a thermal gate timeout included; `preflight.py --end` refusing an end trace without rails with `no_rails`, `energy.yaml` unchanged): the run goes on with every process's measured data and `idle_start_only`; `problems` gets `energy_failed: the end idle reading: <message>` and `idle_start_only: no end idle reading; …`.

## Traces

| capture | source |
|---|---|
| `measured` | Jetpack per-case Perfetto traces, pulled from the androidx media directory |
| `dry` | host Perfetto session around `EnergyDryBenchmark` from `apps/benchmark-runner/energy/energy.pbtx` |

- `energy.pbtx`: 16384 KB ring buffer, power rails every 100 ms, `atrace_apps io.github.junekim0007.cryptobench`, `process_stats`, `write_into_file` every 2500 ms, max 3600000 ms.
- Traces are pulled after every case (`traces:    <case>: <n> pulled`, with `, <m> expected` when fewer arrived): a case's own process may remove the earlier cases' traces on the device. Jetpack's own trace config records memory counters; an allocating call floods the trace, and rails in it are lost as `window_uncovered`. The energy pass's `samples` shorten the window; a trace above 32 MiB is flagged `traceLarge`; a lost window is `window_uncovered` with no number, never a wrong one.
- Rails are counter tracks named `power.%`, cumulative µJ, keyed by their source arg `raw_name`; a track without one, or a `raw_name` seen twice, is `rail_unidentified: <track>: …` (a `measured` case's `trace_unreadable`, a whole dry or pre-flight step's failure). Summed rails: every rail except those whose `subsystem_name` is listed in `apps/benchmark-runner/energy/rails/excluded.yaml` (`Battery`: the channel measures the battery's supply into the system, not a load, and double-counts under load); a rail with no or an unlisted subsystem is summed. The sum leaves out regulator conversion losses, so it is below whole-device energy. A missing or malformed catalog stops the step with `rails_catalog: <path>: <problem>`; every rail excluded reads as no rails. Window edges are interpolated linearly; a window outside the samples of any rail, summed or excluded, is `window_uncovered`, one that ends before it starts `empty_window`; `measured` windows shift by BOOTTIME − MONOTONIC, taken from the first clock snapshot holding both (a trace can open with BOOTTIME alone); exactly one timed phase per case is required.

## Outputs

`benchmark/energy.json`: top level `schemaVersion` 4, `source`, `kind` (`measured` for rails, `estimated` for manafa), `cases`; rails adds `railsResponsive`, `idleBaseline` (`interpolated` or `idle_start_only`) and `excludedSubsystems` (the catalog's list), manafa adds `powerProfile`. `ConvertKt` copies `idleBaseline` onto each case's `energyJ` in `benchmark.json` ([results.md](results.md)).

| case field | value |
|---|---|
| `joules` | gross energy over the window, summed rails |
| `netJoules` | gross − `idleJoules` |
| `idleJoules` | rails: interpolated idle power at the window's midpoint × window length |
| `operations` | see capture modes |
| `joulesPerOperation` | net / operations |
| `windowSeconds`, `polls`, `shortWindow`, `rails`, `capture`, `clockOffsetNs` | window facts; `rails`: joules per summed rail by `raw_name` |
| `excludedRails`, `excludedShare`, `excludedHigh` | joules per excluded rail by `raw_name`; their total / `joules` (null when `joules` is 0); share above 5% (`EXCLUDED_HIGH` in `apps/benchmark-runner/energy/energy.py`: the supply side carried load, e.g. a USB-limited charger), printed `flagged:` |
| `heatSleepAfterKeptRuns` | `measured`: Jetpack slept for heat after the kept runs began; it keeps such runs once its sleeps are spent, so they may be hot; printed `flagged:` |
| `traceBytes`, `traceLarge` | `measured`: the trace's size; large above 32 MiB (`LARGE_TRACE_BYTES` in `apps/benchmark-runner/energy/energy.py`), where rail samples can be lost; printed `flagged:` |
| `valid`, `invalid` | judgement and reasons |

| invalid reason | condition |
|---|---|
| `rails_unresponsive` | rails not responsive |
| `window_uncovered` | the timed phase reaches past the first or last rail sample; the case has no number, the run goes on |
| `short_window` | < 20 polls (`MIN_POLLS` in `apps/benchmark-runner/energy/energy.py`) |
| `net_not_positive` | `netJoules` ≤ 0 |
| `no_operations` | `operations` is 0 or absent |
| `no_joules_per_operation` | `joulesPerOperation` is null and no other reason applies, so a valid case always has a number |
| `trace_not_pulled` | `measured`: the case's Jetpack trace is not in `traces/` |
| `trace_unreadable: <error>` | `measured`: the trace processor failed on the case's trace |
| `timed_phases: <n>` | `measured`: not exactly one timed phase |
| `no_measurement_slices` | `measured`: the timed phase has no `measurement 0` child |
| `no_clock_snapshot` | `measured`: no BOOTTIME/MONOTONIC snapshot in the trace |
| `no_call_count` | `dry`: a marker without its line in `energy-dry.yaml` |
| `no_rails` | the trace has no summed `power.%` counter |
| `empty_window` | the window ends before it starts |
| `not_measured: <reason>` | manafa gave no number: [energy-manafa.md](energy-manafa.md#not-measured); the case-level reasons above reach manafa the same way |

- A case without a window keeps `operations` and holds its reason in `notMeasured`; `joules`, `joulesPerOperation`, `windowSeconds` are null, `clockOffsetNs` is null when no trace was read.
- One case's problem is that case's reason; `energy.py` exits 0 and writes every other case. An energy step that fails as a whole (the source's window around a timed process, trace pull, dry pass beside a timed run, `energy.py` or manafa's answer) prints `warning: energy_failed: <message>`, adds the line to `manifest.yaml` `problems`, and leaves no `energy.json` for that process; `ConvertKt` still writes the timing.
- `ConvertKt` joins valid `measured` cases into `benchmark.json` as `energyJ` (runs = [`joulesPerOperation`], iterations = `operations`, `source`, `kind`); `MergeRunsKt` carries `source`, `kind` and `idleBaseline`; processes with different `source` or `kind` fail with `energy_kinds_differ` or `energy_sources_differ`, different `idleBaseline` merge as `mixed`.
- An estimated run: `manifest.yaml` top-level `energy`, a closing line in `analysis/summary.md`, `(estimated)` on its `energyJ` chart.
- Other `measured` cases print `energy_not_joined: <id>: <reasons>` (`unjudged` when no reason; `missing_field: joulesPerOperation`, `out_of_range: operations <n>` for a valid case without a usable number).
- An `energy.json` `ConvertKt` cannot read (another `schemaVersion` is `unsupported_schema_version`) prints `energy_not_joined: <file>: <message>`; the timing converts without energy.

## Files

```
apps/benchmark-runner/energy/capture.py : resolves a node's capture and source against the default
apps/benchmark-runner/energy/energy.pbtx : Perfetto config for the dry host session
apps/benchmark-runner/energy/energy.py : rail traces to energy.json; the case windows both sources read
apps/benchmark-runner/energy/manafa_estimate.py : joules per case window from a stopped EManafa, or not_measured
apps/benchmark-runner/energy/manafa_session.py : the process holding one EManafa; the manafa pre-flight check
apps/benchmark-runner/energy/preflight.py : idle and busy traces to energy.yaml; the end idle reading into it
apps/benchmark-runner/energy/rails/ : cumulative counter arithmetic; trace queries for rails, markers, timed phases, clock offset; the summed and excluded rails by the excluded.yaml catalog
apps/benchmark-runner/energy/requirements-manafa.txt : manafa, pinned; optional
apps/benchmark-runner/energy/requirements.txt : perfetto, pyyaml
apps/benchmark-runner/energy/tests/ : capture, counters, window, preflight, judge, rail selection and source tests; a fake manafa; recorded rails output; a real busy trace cut to its rails
lib/cryptobench/cryptobench/stages/measurement/energy/session.py : starts, stops and pulls Perfetto sessions on the device
lib/cryptobench/cryptobench/stages/measurement/energy/sources/ : one adapter per energy.source on the host; how the host runs apps/benchmark-runner/energy
lib/cryptobench/cryptobench/stages/measurement/energy/steps.py : capture selection, the run's one source
```

| command | arguments |
|---|---|
| `preflight.py` | `<idle.pftrace> <busy.pftrace> <idle seconds> <busy seconds> <out energy.yaml> [--accept-unresponsive] [--skin <json>]`; `--end <idle-end.pftrace> <idle seconds> <energy.yaml> [--skin <json>]` adds the end reading |
| `energy.py` | `--capability F -o OUT [--prepared --benchmark-data --traces] [--dry-trace --dry-calls]` |
| `manafa_session.py` | `[--check <seconds> --capability <energy.yaml>]`, the source passing `run.energyIdleSeconds`; without them, stdin `stop`, then a JSON list of `energy.py`'s arguments |

- Without `--energy-python`, a run whose interpreter lacks the source's module (`perfetto`, `manafa`) installs `energy/requirements.txt` (+ `requirements-manafa.txt` for manafa) on first use into `$XDG_CACHE_HOME/cryptobench/energy/<source>-<digest>/` (default `~/.cache`) and runs the source there; a changed requirements file is a new folder; a failed install is `energy_install_failed: <source>: <pip's last line>` and leaves nothing; an explicit `--energy-python` without the module is `missing_dependency: <module> in --energy-python <python>`.
