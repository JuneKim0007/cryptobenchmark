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
