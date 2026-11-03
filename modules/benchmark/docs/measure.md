# measure

Prepared cases to measurements and `benchmark.json`. Device harness: `modules/android/docs/harness.md`. File map: [index.md](index.md).

## Flow

```
PreparedRun -> PlanCheck -> refusals -> onRefusal (default: throw RefusedPlanException)
            -> per unrefused case: Invocations.of(prepared) -> HostHarness -> CaseMeasurement -> BenchmarkJson -> benchmark.json
device: benchmarkData.json + prepared.yaml -> JetpackResults -> benchmark.json
per process benchmark.json -> Merge -> benchmark.json
```

Nothing here builds a call: the timed call is the `Invocation` preparation proved with `once()`.

## Refusals

`PlanCheck` runs before any measurement. Installed providers are read from `Security.getProviders()` on the running device or JVM at check time.

| reason | cause |
|---|---|
| `nothing_to_measure` | the plan has no cases |
| `not_positive: processRepetitions <n>` | no run asked for |
| `duplicate_case: <n> cases share this id` | two cases share an id |
| `provider_not_installed: <p>, installed [..]` | provider absent here |
| `not_measurable: <type> has no operation this harness can time` | a TYPE_DEFAULT case |
| `not_positive: iterations <n>`, `not_positive: inputSize <n>` | unmeasurable setting |
| `not_supported: metrics [..], this harness measures [..]` | a case's `metrics` outside the harness's set: host `HostHarness.METRICS` = `[TIME]`; device `JetpackConfig.METRICS` = all three |
| energy refusals | `docs/energy.md` |

| rule | value |
|---|---|
| default `onRefusal` | throws `RefusedPlanException` `refused_plan: ...`; nothing is measured |
| non-throwing `onRefusal` | refused case ids are filtered out; the rest are measured |
| `runnable(run)` | refused cases left out with their refusal; a run-wide refusal or no case left throws `RefusedPlanException`; the device plan's rule |
| `Refusal.toString` | `<caseId>: <reason>`; bare reason when run-wide |

## What one sample is

Host (`HostHarness`):

| step | value |
|---|---|
| warm-up | `TimedLoop` for 200 ms (`WARMUP_NANOS`), discarded |
| inner loop count | 30 ms (`RUN_NANOS`) / warm-up ns per call, min 1 |
| samples | `harness.iterations`, else 5 (`RUNS`) |
| one sample | elapsed ns / inner loop count; results passed to `BlackHole` |
| row | `timeNs` only; `keyKind` = recipe kind; `parameters` = the prepared case's `resolvedParameters`; median = middle or mean of the two middles |

`TimedLoop` calls `once()` until the budget is spent and returns the call count. The host loop locks no clocks and reads no thermal state. `processRepetitions` is one process per repetition, run by the caller: `docs/run.md`.

## CaseSettings

Harness settings as plain values, no androidx type.

| field | value |
|---|---|
| `iterations`, `warmupIterations` | from `HarnessSettings` |
| `profiling` | null or `none`: `NONE`; `MethodTracing`: `METHOD_TRACING`; `StackSampling`: `STACK_SAMPLING`; else `invalid: profiling <name>` |
| `energy` | `Energy.of(harness.energy)`; default `Energy.NONE` |
| `cpu` | `harness.cpu` |
| `metrics` | the case's `metrics` (`run.metrics`); `TIME` always present |

## benchmark.json

| key | holds |
|---|---|
| `runtime` | string map |
| `cases[]` | `id`, `type`, `algorithm`, `provider`, `operation`, `keySize`, `inputSize`, `keyKind`, `parameters`, `metrics` |
| `metrics.<key>` | `iterations`, `runs[]`, optional `reported{minimum, maximum, median, coefficientOfVariation}` |

| rule | value |
|---|---|
| metric keys | `timeNs`, `allocationCount`, `instructions`, `cpuCycles`, `branchMisses` (`CPU_EVENTS`), `energyJ` (with `source` and `kind`) |
| reported metrics | only the case's `run.metrics` (`MetricKeys.of`), plus `energyJ` from `tools/energy`; the device may measure more: [Jetpack conversion](#jetpack-conversion) |
| `timeNs` | required in every row |
| `keyKind` | `secret`, `pair`, `none` |
| `parameters` | what the provider used; keys and meaning as prepared.yaml `resolvedParameters` (`modules/preparation/docs/prepared.md`); `{}` when nothing applies; required |
| `runs` | doubles; non-finite: `not_finite: runs` |
| `iterations` | `>= 1` |
| `reported` | dropped when any of the four numbers is missing |
| readers | `Merge`: a case without `metrics` or `parameters` fails `missing_field: metrics for <id>` or `missing_field: parameters for <id>` |

## Merge

| rule | value |
|---|---|
| runs | concatenated per case id and metric, in input order |
| `iterations` | the first process's |
| `reported` | dropped |
| partial presence | a case or metric present in only some processes survives |
| `runtime` keys | first value wins |
| `parameters` | must be equal across processes, else the case is left out: `not_merged: <id>: different_parameters: <id>: <a> and <b>`; energy of different kinds or sources the same |
| a process entry without `metrics` or `parameters` | that entry is left out: `not_merged: <id>: process <n>: missing_field: ...`; the other processes keep the case |
| no case left | `MergeRunsKt` stops with `nothing_merged` |

## Jetpack conversion

| rule | value |
|---|---|
| join key | text inside `[...]` of `benchmarks[].name` = case id in `prepared.yaml` |
| no plan case | `dropped` line `not_in_plan: <id>` |
| no metrics | `dropped` line `no_metrics: <id>` |
| any other problem with one case | `dropped` line `not_converted: <id>: <message>`; the other cases convert |
| no row at all | `ConvertKt` stops with `nothing_converted` |
| carried metrics | the `prepared.yaml` case's `metrics`, as `MetricKeys.of`; others androidx wrote are dropped; the only place `run.metrics` filters device rows |
| ALLOCATION not requested | androidx still runs its allocation phase and writes `allocationCount`; it is not reported |
| a requested metric absent | `not_converted: <id>: missing_field: metrics.<key> for <id>; androidx wrote [..]` |
| case without `metrics` | `not_converted: <id>: missing_field: metrics for <id>` |
| `timeNs.iterations`, CPU event `iterations` | `repeatIterations`, default 1 |
| `allocationCount.iterations` | 1 |
| case shape | algorithm, provider, operation, sizes, `keyKind` from the `prepared.yaml` case |
| `parameters` | the case's `resolvedParameters`; absent: `not_converted: <id>: missing_field: resolvedParameters for <id>; prepared.yaml predates schemaVersion 2` |
| androidx.benchmark | 1.5.0 |

| `runtime` key | Jetpack source |
|---|---|
| `model`, `fingerprint` | `context.build` |
| `sdkInt` | `context.build.version.sdk` |
| `jetpackCpuLocked` | `context.cpuLocked` |
| `sustainedPerformanceModeEnabled`, `compilationMode` | `context` |
| `thermalThrottleSleepSeconds` | sum over benchmarks |

| `RunCountAudit` line | when |
|---|---|
| `iterations_not_applied: <id> asked for N, timeNs has M runs` | timing runs differ from requested iterations |
| `allocation_runs_changed: ...` | allocation runs differ from 5 |

`ConvertKt` and `MergeRunsKt` command lines: `docs/tools.md`.

## Energy

Capture modes, `energy.yaml`, `energy.json`, `energyJ` join and energy refusals: `docs/energy.md`.

## Example

`example/` holds a `benchmarkData.json` and its `prepared.yaml`; `JetpackResultsTest` converts them and compares inline `benchmark.json` text.
