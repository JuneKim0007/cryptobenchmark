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
`Invocation.setUp` is the per-iteration work that must not be timed.

## What one sample is

| | Host (`HostHarness`) | Device (`BenchmarkRule`) |
|---|---|---|
| warmup | 200 ms of calls, discarded | Jetpack's, until the timing is stable |
| one sample | loops for 30 ms, reports the mean call | Jetpack's inner loop, reported per iteration |
| samples per case | `harness.iterations`, else 5 | `harness.iterations`, else 50 |
| untimed per iteration | `setUp()` inside the timed block | `runWithMeasurementDisabled { setUp() }` |
| result | `benchmark.json` | `benchmarkData.json` |

`iterations` is how many samples a case yields, not how many calls one sample makes: the inner loop
comes from a time budget, so a 40 ns digest is not measured against the clock's resolution.

## Jetpack's output → `benchmark.json`

`androidx.benchmark` writes `<package>-benchmarkData.json`, verified against 1.5.0:

| Jetpack | Used as |
|---|---|
| `benchmarks[].name` = `measure[<case id>]` | the join key into `prepared.yaml` |
| `benchmarks[].metrics.timeNs.runs` | `nanosPerOperation` |
| `benchmarks[].repeatIterations` | `iterations` — the calls one sample loops |
| `benchmarks[].thermalThrottleSleepSeconds` | summed into the runtime: the device paused mid-run |
| `context.cpuLocked`, `context.sustainedPerformanceModeEnabled`, `context.compilationMode` | the runtime: whether the numbers are comparable |
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
| `HostHarness`, `CaseMeasurement`, `BlackHole` | `run` | the host loop, one case's samples, the sink |
| `BenchmarkJson` | `report` | `benchmark.json` for `tools/quick-bench/analyze.py` |

## Limits

- The host loop locks no clocks and reads no thermal state: a host number is a shape, not a device number.
- Jetpack writes `benchmarkData.json`; converting it into `benchmark.json` for the analysis is not done yet.
- `processRepetitions` is the runner's job: one process per repetition, not a loop in here.
