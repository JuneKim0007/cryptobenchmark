# measure

Prepared cases → measurements. The only module that runs inside a timed region.

## Flow

```
PreparedRun ─► PlanCheck ─► refusals, dropped ─────────────┐
                    │                                      │
                    └─► per case: Invocations.of(prepared) ─┴─► HostHarness or BenchmarkRule ─► CaseMeasurement
                                                                                                    │
                                                                                          BenchmarkJson ─► benchmark.json
```

Nothing here builds a call. `Invocation.perIteration` is what preparation proved runs, and
An invocation is one timed call. Per-iteration specs (`fresh(n)`) come from a pool drawn before the timer; the call only indexes it, so nothing is paused per iteration.

## What one sample is

| | Host (`HostHarness`) | Device (`BenchmarkRule`) |
|---|---|---|
| warmup | 200 ms of calls, discarded | Jetpack's, until the timing is stable |
| one sample | loops for 30 ms, reports the mean call | Jetpack's inner loop, reported per iteration |
| samples per case | `harness.iterations`, else 5 | `harness.iterations`, else 50 |
| result | `benchmark.json` | `benchmarkData.json` |

`iterations` is how many samples a case yields, not how many calls one sample makes: the inner loop
comes from a time budget, so a 40 ns digest is not measured against the clock's resolution.

A case carries one block per metric, not one sample list: Jetpack measures `timeNs` over 50 runs of
`repeatIterations` calls and `allocationCount` over 5 runs it has already divided by its own,
shorter loop, so neither the run count nor the iteration count is shared. The timing is also written
flat as `iterations`/`nanosPerOperation` — a deliberate duplication, kept until `analyze.py` and
`Merge` read `metrics` instead. The host loop writes only `timeNs`: `System.nanoTime` cannot count
allocations, and an absent key says that where a zero would not.

Samples are fractional. Jetpack reports nanoseconds per operation as a double, and cutting it to an
integer biases fast operations low (on the 163-case emulator run, up to 0.46% on 190–250 ns
operations, and more the faster the operation). `runs` is written as doubles, and a sample that is not
a finite number is refused.

Each metric block also carries `reported`: the `minimum`, `maximum`, `median` and
`coefficientOfVariation` androidx wrote for those runs, so analysis can check its own statistics
against the library's (`charts.py` lists any case above 1e-9 relative in `manifest.yaml`). It describes
one process's runs, so it is present for a single process and dropped by a merge. A block without all
four numbers carries none.

## What the device run applies

The harness settings in the plan reach Jetpack per case, through `MicrobenchmarkConfig`
(`JetpackConfig`, from `CaseSettings`). Not everything can be set, and the limits are the library's:

| Plan setting | Goes to | Limit |
|---|---|---|
| `harness.iterations` | `measurementCount` | the timing phase only. The allocation phase is always 5 runs. The instrumentation argument `androidx.benchmark.iterations`, if you pass it, wins over this: the library's code reads `Arguments.iterations ?: config.measurementCount`, whatever its KDoc says |
| `harness.warmupIterations` | `warmupCount` | at least 1: androidx refuses 0, so `CaseSettings` does too. Leave it out to let the library decide |
| `harness.profiling` | `ProfilerConfig` | `MethodTracing` or `StackSampling`, run after the timing phase. `none` is a null config, which androidx replaces with its own default (`MethodTracing`); `--device` therefore launches with `androidx.benchmark.profiling.mode=None` so `none` means none |
| `harness.energy` | `CaseRuns` (see Energy) | `measured`: Jetpack's run, cooled down after; `dry`: `EnergyDryBenchmark`, not Jetpack |
| `metrics: TIME` | — | always measured |
| `metrics: ALLOCATION` | — | always measured, in its own phase; listing only `TIME` does not switch it off |
| `metrics: CPU_EVENTS` | launch argument `androidx.benchmark.cpuEventCounter.enable=true` | the capture class is internal to androidx, so it is a whole-run switch, not per case. `scripts/device_args.py` prints it. Needs a rooted device |

After a run, `ConvertKt` prints `iterations_not_applied: <case> asked for N, timeNs has M runs` for any case whose
runs differ from what the plan asked for, and `allocation_runs_changed:` if androidx stops using 5. A setting that
never reached the timer is named, not left to a plan that claims it.

## Energy

Joules per case from the device's power rails (ODPM), read from Perfetto traces by `tools/energy`.
Rails are cumulative energy counters (µWs = µJ since boot); a window's energy is the counter at its end
minus at its start, interpolated between polls. No voltage, current or power is recorded.

| `harness.energy.capture` | Run | Window | Operations | Trace |
|---|---|---|---|---|
| `none` | `CryptoBenchmark` | — | — | — |
| `measured` | `CryptoBenchmark`, then `Cooldown` | Jetpack's `Benchmark Time` slice, after its last thermal sleep | `repeatIterations` × timing runs | Jetpack's per-case trace (rails every 250 ms) |
| `dry` | `EnergyDryBenchmark`: `Cooldown(Rewarm(EnergyWindow(DryLoopRun)))` | the case's `energy:<id>` atrace section | calls `DryLoopRun` counted | one host session, `tools/energy/energy.pbtx` (rails every 100 ms) |

| Field | Default | Meaning |
|---|---|---|
| `windowSeconds` | 10 | dry: loop length |
| `warmupSeconds` | 2 | dry: re-warm before each window, outside it |
| `cooldownSeconds` | 5 | idle after each energy case |

- Net joules subtract the pre-flight's idle energy for a window of the same length.
- A case is joined into `benchmark.json` as `energyJ` (joules per operation) only when `energy.json` judges it
  `valid`; otherwise `ConvertKt` prints `energy_not_joined: <case>: <reasons>`.

| Reason | Means |
|---|---|
| `rails_unresponsive` | the pre-flight saw equal energy idle and under load on every core |
| `short_window` | fewer than 20 rail polls inside the window |
| `net_not_positive` | the window used no more than the idle baseline |

Refusals, before any timer, for a run with an energy case:

| Reason | Means |
|---|---|
| `energy_capability_unknown` | no `energy.yaml` was pushed |
| `no_power_rails` | the device reports no rail |
| `rails_unresponsive` | the rails ignore load; `--energy-accept-unresponsive` admits them for plumbing runs |

## Jetpack's output → `benchmark.json`

`androidx.benchmark` writes `<package>-benchmarkData.json`, verified against 1.5.0:

| Jetpack | Used as |
|---|---|
| `benchmarks[].name` = `measure[<case id>]` | the join key into `prepared.yaml` |
| `benchmarks[].metrics.timeNs.runs` | `metrics.timeNs.runs`, and the flat `nanosPerOperation` |
| `benchmarks[].repeatIterations` | `metrics.timeNs.iterations` — the calls one timed sample loops |
| `benchmarks[].metrics.allocationCount.runs` | `metrics.allocationCount.runs` — 5 runs, already per operation |
| `benchmarks[].thermalThrottleSleepSeconds` | summed into the runtime: the device paused mid-run |
| `context.cpuLocked` | `runtime.jetpackCpuLocked`: Jetpack's guess (no core's floor at its lowest step), true on a vendor-raised floor with scaling clocks; the manifest's `cpuLocked` is read from sysfs instead (`scripts/clocks.py`) |
| `context.sustainedPerformanceModeEnabled`, `context.compilationMode` | the runtime: whether the numbers are comparable |
| `context.build.model`, `fingerprint`, `version.sdk` | the runtime: which device |

Jetpack knows how long a name took, not what it measured. Algorithm, provider, operation and sizes
come from the `prepared.yaml` written on the same device. A measurement with no case in the plan is
reported as `no_case_in_the_plan: <id>`, never guessed at.

```
adb pull /sdcard/Android/media/io.github.junekim0007.cryptobench/<package>-benchmarkData.json
../jca-contract/gradlew -p tools/quick-bench run -q -PmainClass=ConvertKt \
  --args="<benchmarkData.json> results/preparation/prepared.yaml results/benchmark"
```

## processRepetitions

One process per repetition, never a loop inside one process: JIT state, heap layout and page
placement are per process, and averaging them away hides the variance the number is supposed to
report. `scripts/pipeline.py` reads `run.processRepetitions` from `effective.yaml`, runs the harness
that many times into `results/benchmark/process-<n>/`, then merges.

Merging concatenates each case's samples in process order and keeps the first process's
`iterations`. A case one process skipped keeps what the others measured.

## Refusals

Checked before the first timer, against the device that will run it — not the one that wrote the plan.

| Reason | Means |
|---|---|
| `nothing_to_measure` | the plan has no cases |
| `not_positive: processRepetitions <n>` | the plan asks for no run |
| `provider_not_installed: <name>` | the plan was prepared somewhere else |
| `not_measurable: <type> has no operation this harness can time` | a `TYPE_DEFAULT` case |
| `not_positive: iterations <n>`, `not_positive: inputSize <n>` | a setting that cannot be measured |
| `duplicate_case: <n> cases share this id` | two cases would overwrite each other in the results |

A refused case is dropped and the rest of the run continues; `RefusedPlanException` is the default
when nothing else handles them.

## On a device

`modules/android/src/androidTest` holds the Jetpack side:

| Class | Does |
|---|---|
| `DevicePlan` | prepares on the device, from the three files pushed to its external files directory |
| `CryptoBenchmark` | one parameterised measurement per prepared case |

```
adb push results/configuration/effective.yaml results/discovery/probe_*.yaml results/discovery/trial_*.yaml \
  /sdcard/Android/data/io.github.junekim0007.cryptobench/files/cryptobench/
ANDROID_HOME=$HOME/Library/Android/sdk ./gradlew :android:connectedReleaseAndroidTest
```

Preparation runs on the device because the providers, the key store and the default key sizes are the
device's own. The capture and trial must come from that same device.

## Classes

| Class | Package | Role |
|---|---|---|
| `Benchmark` | root | check, then measure what was not refused |
| `RefusedPlanException` | root | the default when refusals are not handled |
| `PlanCheck`, `Refusal` | `check` | what this device will not run, by name |
| `EnergyCapability` | `check` | the pre-flight's view of the rails (`energy.yaml`), and the refusal it implies |
| `HostHarness`, `CaseMeasurement`, `BlackHole` | `run` | the host loop, one case's samples, the sink |
| `CaseSettings` | `run` | what one case asks of the timer and the energy capture, with no androidx type |
| `TimedLoop` | `run` | calls an invocation for a duration; shared by host warm-up, re-warm and the dry loop |
| `CaseRun`, `CaseRuns` | `run.compose` | one case's run, and the factory that composes it from the energy capture |
| `DryLoopRun` | `run.compose` | the energy-only loop: calls counted, nothing timed |
| `Cooldown`, `Rewarm`, `EnergyWindow` | `run.decorate` | decorators: idle after, warm before, bracket with a trace marker |
| `Energy`, `WindowMarker` | `run.energy` | a case's energy settings with defaults; the marker port the device implements |
| `BenchmarkJson`, `ResultRow` | `report` | `benchmark.json` for `tools/quick-bench/analyze.py`, and one case in it |
| `MetricSamples` | `report` | one metric's runs, the iteration count they were measured at, and what androidx reported for them |
| `ReportedStats` | `report` | androidx's own `minimum`, `maximum`, `median`, `coefficientOfVariation` for one process's runs |
| `Merge` | `report` | one `benchmark.json` per process joined |
| `CaseDocument` | `report` | the one reader every report uses: mapping, case list, samples, row |
| `JetpackResults`, `RunCountAudit` | `report.jetpack` | `benchmarkData.json` converted; requested iterations against the runs a result carries |
| `EnergyWindows` | `report.energy` | `energy.json` → `energyJ` for valid measured cases; the invalid ones by reason |

## Limits

- The host loop locks no clocks and reads no thermal state: a host number is a shape, not a device number.
- `processRepetitions` is the runner's job: one process per repetition, not a loop in here.
