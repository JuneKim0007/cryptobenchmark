# Benchmark

> An independent module that times the cases preparation built, and refuses a plan this device cannot run.

## Responsibilities

- Check the plan before any timer starts: installed providers, measurable operations, one id per case.
- Time each case through `Invocations.of(prepared)`: the call preparation already proved runs.
- Write `benchmark.json` for the analysis step, from this harness or from Jetpack's own output.
- Join the samples of one process per `processRepetitions`, so process-to-process variance stays visible.
- Compose a case's run from its energy capture (`CaseRuns`): unchanged, cooled down after Jetpack, or a dry
  energy window; refuse energy cases on a device whose rails are absent or do not respond to load.

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
    - `Benchmark.kt` : check, then measure what was not refused
    - `RefusedPlanException.kt` : the default when refusals are not handled
    - `check/`
      - `EnergyCapability.kt` : the rails the pre-flight saw, and the refusal they imply
      - `PlanCheck.kt` : what this device will not run, by name
      - `Refusal.kt` : one refused case and its reason
    - `report/`
      - `BenchmarkJson.kt` : writes `benchmark.json`
      - `CaseDocument.kt` : the reader every report uses
      - `Merge.kt` : joins one `benchmark.json` per process
      - `MetricSamples.kt` : one metric's runs and their iteration count
      - `ReportedStats.kt` : androidx's own statistics for one process
      - `ResultRow.kt` : one case in `benchmark.json`
      - `energy/`
        - `EnergyWindows.kt` : `energy.json` → `energyJ`, valid measured cases only
      - `jetpack/`
        - `JetpackResults.kt` : `benchmarkData.json` + `prepared.yaml` → rows
        - `RunCountAudit.kt` : requested iterations against the runs a row carries
    - `run/`
      - `BlackHole.kt` : the host sink
      - `CaseMeasurement.kt` : one case's host samples
      - `CaseSettings.kt` : what a case asks of the timer and the energy capture
      - `HostHarness.kt` : the host timing loop
      - `TimedLoop.kt` : calls an invocation for a duration
      - `compose/`
        - `CaseRun.kt` : one case's run
        - `CaseRuns.kt` : composes a run from its energy capture
        - `DryLoopRun.kt` : the energy-only, counted loop
      - `decorate/`
        - `Cooldown.kt` : idles after a run
        - `EnergyWindow.kt` : brackets a run with a trace marker
        - `Rewarm.kt` : warms before a run
      - `energy/`
        - `Energy.kt` : energy settings with defaults
        - `WindowMarker.kt` : the marker port the device implements
  - `src/test/kotlin/`
    - `BlackHoleTest.kt`
    - `CaseDocumentTest.kt`
    - `EnergyCheckTest.kt`
    - `EnergyRunTest.kt`
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
