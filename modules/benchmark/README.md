# Benchmark

> An independent module that times the cases preparation built, and refuses a plan this device cannot run.

## Responsibilities

- Check the plan before any timer starts: installed providers, measurable operations, one id per case.
- Time each case through `Invocations.of(prepared)`: the call preparation already proved runs.
- Write `benchmark.json` for the analysis step.

  1. For more information, refer to <measure.md>.

## File Structure

- `benchmark/`
  - `build.gradle`
  - `README.md`
  - `docs/`
    - `measure.md`
  - `src/main/kotlin/`
    - `Benchmark.kt`
    - `RefusedPlanException.kt`
    - `check/`
      - `PlanCheck.kt`
      - `Refusal.kt`
    - `report/`
      - `BenchmarkJson.kt`
    - `run/`
      - `BlackHole.kt`
      - `CaseMeasurement.kt`
      - `HostHarness.kt`
  - `src/test/kotlin/`
    - `HostHarnessTest.kt`
    - `PlanCheckTest.kt`

## Limitations

- The one module that depends on another: it times `preparation`'s `Invocation`, so it is built with it.
  It needs neither `config` nor `discovery`, which `tools/module-isolation` checks.
- `HostHarness` is a stand-in: no clock locking, no thermal gate, no separate process per repetition.
  On a device those are Jetpack's, driven from `modules/android/src/androidTest`.
- A refused case is dropped, not measured. Nothing here re-resolves a case: what preparation built is
  what runs.
