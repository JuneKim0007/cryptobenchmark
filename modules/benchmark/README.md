# Benchmark

> An independent module that times the cases preparation built, and refuses a plan this device cannot run.

## Responsibilities

- Check the plan before any timer starts: installed providers, measurable operations, one id per case.
- Time each case through `Invocations.of(prepared)`: the call preparation already proved runs.
- Write `benchmark.json` for the analysis step, from this harness or from Jetpack's own output.
- Join the samples of one process per `processRepetitions`, so process-to-process variance stays visible.

  1. For more information, refer to <measure.md>.

## File Structure

- `benchmark/`
  - `build.gradle`
  - `README.md`
  - `docs/`
    - `measure.md`
  - `example/`
    - `benchmark_jetpack_example.json`
    - `benchmark_prepared_example.yaml`
  - `src/main/kotlin/`
    - `Benchmark.kt`
    - `RefusedPlanException.kt`
    - `check/`
      - `PlanCheck.kt`
      - `Refusal.kt`
    - `report/`
      - `BenchmarkJson.kt`
      - `JetpackResults.kt`
      - `Merge.kt`
      - `ResultRow.kt`
    - `run/`
      - `BlackHole.kt`
      - `CaseMeasurement.kt`
      - `HostHarness.kt`
  - `src/test/kotlin/`
    - `HostHarnessTest.kt`
    - `JetpackResultsTest.kt`
    - `MergeTest.kt`
    - `PlanCheckTest.kt`

## Limitations

- The one module that depends on another: it times `preparation`'s `Invocation`, so it is built with it.
  It needs neither `config` nor `discovery`, which `tools/module-isolation` checks.
- `HostHarness` is a stand-in: no clock locking, no thermal gate, no separate process per repetition.
  On a device those are Jetpack's, driven from `modules/android/src/androidTest`.
- A refused case is dropped, not measured. Nothing here re-resolves a case: what preparation built is
  what runs.
- A Jetpack measurement is joined to a case by id from `prepared.yaml`: without that file the numbers
  have no algorithm, provider or size.

## Example

`example/` is one device run: Jetpack's `benchmarkData.json` and the `prepared.yaml` beside it.
`JetpackResultsTest` converts them and compares the `benchmark.json` the analysis reads.
