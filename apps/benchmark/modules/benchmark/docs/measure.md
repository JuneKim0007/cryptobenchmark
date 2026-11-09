# measure

Prepared cases to measurements and `benchmark.json`. Device harness: `apps/benchmark/modules/android/docs/harness.md`. Energy capture, `energy.yaml`, `energy.json` and the `energyJ` join: `docs/energy.md`. File map: [index.md](index.md).

## Flow

```
RunnablePlan: Preparation.list -> PlanCheck.runnable -> refused cases to skipped.yaml (host and device)
            -> per runnable case: Preparation.prepareOne -> Invocations.of(prepared) -> HostHarness -> CaseMeasurement -> BenchmarkJson -> benchmark.json, rewritten whole after each case
device: benchmarkData.json + prepared.yaml -> JetpackResults -> benchmark.json
per process benchmark.json -> Merge -> benchmark.json
```

Nothing here builds a call: the timed call is the `Invocation` preparation proved with `once()`.

## Refusals

`PlanCheck` runs on the listed cases, before any is prepared or measured. Installed providers are read from `Security.getProviders()` on the running device or JVM at check time.

| reason | cause |
|---|---|
| `nothing_to_measure` | the plan has no cases |
| `not_positive: processRepetitions <n>` | no run asked for |
| `duplicate_case: <n> cases share this id` | two cases share an id |
| `provider_not_installed: <p>, installed [..]` | provider absent here |
| `not_measurable: <type> has no operation this harness can time` | a TYPE_DEFAULT case |
| `not_supported: metrics [..], this harness measures [..]` | a case's `metrics` outside the harness's set: host `HostHarness.METRICS` = `[TIME]`; device `JetpackConfig.METRICS` = all three |
| energy refusals | `docs/energy.md` |

| rule | value |
|---|---|
| `runnable(cases, processRepetitions)` | the one rule, host (`BenchKt`, `CheckKt`) and device: refused cases left out with their refusal, added to `skipped.yaml` (stage `benchmark`, reason `<caseId>: <refusal>`); a run-wide refusal or no case left throws `RefusedPlanException` `refused_plan: ...` |
| `Refusal.toString` | `<caseId>: <reason>`; bare reason when run-wide |

## What one sample is

Host (`HostHarness`):

| step | value |
|---|---|
| warm-up | `TimedLoop` for 200 ms (`WARMUP_NANOS`), discarded |
| inner loop count | 30 ms (`RUN_NANOS`) / warm-up ns per call, min 1 |
| samples | `harness.iterations`, else 5 (`RUNS`) |
| one sample | elapsed ns / inner loop count; results passed to `BlackHole` |
| collection | a forced GC and finalization before each sample, timer stopped; none during the warm-up |
| row | `timeNs`, `gcCleanNs` and `gcCount` per sample; `keyKind` = recipe kind; `variant` = the case's; `parameters` = the prepared case's `resolvedParameters`; median = middle or mean of the two middles |

`TimedLoop` calls `once()` until the time is spent and returns the call count. The host loop locks no clocks and reads no thermal state. `processRepetitions` is one process per repetition, run by the caller: `docs/run.md`.

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
| `cases[]` | `id`, `type`, `algorithm`, `provider`, `operation`, `keySize`, `inputSize`, `keyKind`, `variant`, `parameters`, `metrics`; the optional heat fields `thermalThrottleSleepSeconds`, `thermal`, `thermalNote`, `gate`: [results.md](../../../../../docs/results.md#benchmarkjson-case-fields) |
| `metrics.<key>` | `iterations`, `runs[]`, optional `reported{minimum, maximum, median, coefficientOfVariation}` |

| rule | value |
|---|---|
| metric keys | `timeNs`, `allocationCount`, `instructions`, `cpuCycles`, `branchMisses` (`CPU_EVENTS`), `energyJ` (with `source` and `kind`) |
| reported metrics | only the case's `run.metrics` (`MetricKeys.of`), plus `energyJ` from `apps/benchmark-runner/energy`; the device may measure more: [Jetpack conversion](#jetpack-conversion) |
| `timeNs` | required in every row |
| `keyKind`, `variant` | `secret`, `pair`, `none`; `"fixed"` or `"notFixed"`, the prepared case's ([operations.md](../../preparation/docs/operations.md#variants)); always written |
| `parameters` | what the provider used; keys and meaning as prepared.yaml `resolvedParameters` (`apps/benchmark/modules/preparation/docs/prepared.md`); `{}` when nothing applies; required |
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
| `runtime` keys | first value wins; a later different value adds a line `runtime_differs: <key>: process 1 <a>, process <n> <b>` |
| run counts | a metric's run count must equal the first process's, else the case is left out: `not_merged: <id>: unequal_samples: ...` |
| `parameters`, `variant` | must be equal across processes, else the case is left out: `not_merged: <id>: different_parameters: <id>: <a> and <b>` (`different_variant: ...`); energy of different kinds or sources the same |
| a process entry without `metrics` or `parameters` | that entry is left out: `not_merged: <id>: process <n>: missing_field: ...`; the other processes keep the case |
| no case left | `MergeRunsKt` stops with `nothing_merged` |

## Pass merge

`PassMerge` (`MergePassesKt`): the base pass's file, plus `<metric key>=<benchmark.json>` per other pass.

| rule | value |
|---|---|
| rows | one per base case, its shape, `variant`, `parameters` and every metric the other passes do not own |
| an owned key | only from its pass's row of the same id; the base pass's value of it is dropped |
| a case its pass lost | no value of that key: `not_merged: <id>: <key>: its pass has no row` |
| no case left | `nothing_merged` |

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
| `allocationSamples` written (an allocation pass) | read as `allocationCount`, one run per sample; `allocation_runs_changed` is not checked |
| a pass (`ConvertKt --metrics=... --samples=n`) | the pass's metrics replace the case's `metrics`; `n` replaces `iterations` in `iterations_not_applied` |
| case shape | algorithm, provider, operation, sizes, `keyKind`, `variant` from the `prepared.yaml` case |
| `parameters` | the case's `resolvedParameters`; absent: `not_converted: <id>: missing_field: resolvedParameters for <id>; ...` |
| androidx.benchmark | 1.5.0 |

| `runtime` key | Jetpack source |
|---|---|
| `model`, `fingerprint` | `context.build` |
| `sdkInt` | `context.build.version.sdk` |
| `jetpackCpuLocked` | `context.cpuLocked` |
| `sustainedPerformanceModeEnabled`, `compilationMode` | `context` |
| `thermalThrottleSleepSeconds` | sum over benchmarks; each case also keeps its own (`docs/results.md`) |

| `RunCountAudit` line | when |
|---|---|
| `iterations_not_applied: <id> asked for N, timeNs has M runs` | timing runs differ from requested iterations |
| `allocation_runs_changed: ...` | allocation runs differ from 5 |

`ConvertKt` and `MergeRunsKt` command lines: `docs/tools.md`.

## Example

`example/` holds a `benchmarkData.json` and its `prepared.yaml`; `JetpackResultsTest` converts them and compares inline `benchmark.json` text.
