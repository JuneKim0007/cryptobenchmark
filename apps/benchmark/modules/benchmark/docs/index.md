# benchmark

```
apps/benchmark/modules/benchmark/.gitignore : ignores /build
apps/benchmark/modules/benchmark/README.md : module summary and link to this index
apps/benchmark/modules/benchmark/build.gradle : Kotlin/JVM 17 library; api :preparation; snakeyaml 2.3; passes examples.update to tests
apps/benchmark/modules/benchmark/docs/index.md : this map
apps/benchmark/modules/benchmark/docs/measure.md : plan check, host harness, benchmark.json, merge, Jetpack conversion
apps/benchmark/modules/benchmark/example/benchmark_jetpack_example.json : example androidx benchmarkData.json
apps/benchmark/modules/benchmark/example/benchmark_prepared_example.yaml : prepared.yaml paired with the Jetpack example
apps/benchmark/modules/benchmark/src/main/kotlin/Benchmark.kt : runs PlanCheck, then measures unrefused cases
apps/benchmark/modules/benchmark/src/main/kotlin/RefusedPlanException.kt : default refusal handler's exception
apps/benchmark/modules/benchmark/src/main/kotlin/check/EnergyCapability.kt : parses energy.yaml; derives the energy refusal
apps/benchmark/modules/benchmark/src/main/kotlin/check/PlanCheck.kt : pre-timer refusals for a PreparedRun; the runnable cases with the refused ones left out
apps/benchmark/modules/benchmark/src/main/kotlin/check/Refusal.kt : one refusal (caseId, reason)
apps/benchmark/modules/benchmark/src/main/kotlin/report/BenchmarkJson.kt : writes benchmark.json text
apps/benchmark/modules/benchmark/src/main/kotlin/report/CaseDocument.kt : shared YAML and JSON reader for case documents
apps/benchmark/modules/benchmark/src/main/kotlin/report/Merge.kt : merges per-process benchmark.json texts; a case that cannot merge is left out with a line
apps/benchmark/modules/benchmark/src/main/kotlin/report/MetricKeys.kt : run.metrics entry to its benchmark.json metric keys
apps/benchmark/modules/benchmark/src/main/kotlin/report/MetricSamples.kt : one metric's runs, iteration count, reported stats; metric key names
apps/benchmark/modules/benchmark/src/main/kotlin/report/PassMerge.kt : one row per case from per-pass files; each owned metric only from its pass
apps/benchmark/modules/benchmark/src/main/kotlin/report/ReportedStats.kt : androidx minimum, maximum, median, CoV for one process
apps/benchmark/modules/benchmark/src/main/kotlin/report/ResultRow.kt : one case row of benchmark.json
apps/benchmark/modules/benchmark/src/main/kotlin/report/energy/EnergyWindows.kt : reads energy.json into energyJ samples and per-case reasons a case is not joined
apps/benchmark/modules/benchmark/src/main/kotlin/report/jetpack/JetpackResults.kt : benchmarkData.json and prepared.yaml to rows, runtime and the dropped cases' lines
apps/benchmark/modules/benchmark/src/main/kotlin/report/jetpack/RunCountAudit.kt : compares requested iterations and allocation runs to actual runs
apps/benchmark/modules/benchmark/src/main/kotlin/run/BlackHole.kt : result sink
apps/benchmark/modules/benchmark/src/main/kotlin/run/CaseMeasurement.kt : one host-measured case: timeNs samples, median
apps/benchmark/modules/benchmark/src/main/kotlin/run/CaseRun.kt : fun interface run(): Long?
apps/benchmark/modules/benchmark/src/main/kotlin/run/CaseSettings.kt : harness settings as plain values, no androidx type
apps/benchmark/modules/benchmark/src/main/kotlin/run/HostHarness.kt : host JVM timing loop
apps/benchmark/modules/benchmark/src/main/kotlin/run/TimedLoop.kt : calls once() until a nanosecond budget is spent; returns the call count
apps/benchmark/modules/benchmark/src/main/kotlin/run/compose/CaseRuns.kt : composes a CaseRun from the energy capture mode
apps/benchmark/modules/benchmark/src/main/kotlin/run/decorate/Cooldown.kt : sleeps after the inner run
apps/benchmark/modules/benchmark/src/main/kotlin/run/decorate/EnergyWindow.kt : brackets the inner run with an energy:<id> marker
apps/benchmark/modules/benchmark/src/main/kotlin/run/decorate/Rewarm.kt : TimedLoop warm-up before the inner run
apps/benchmark/modules/benchmark/src/main/kotlin/run/energy/Energy.kt : energy settings with defaults
apps/benchmark/modules/benchmark/src/main/kotlin/run/energy/WindowMarker.kt : begin and end marker port
apps/benchmark/modules/benchmark/src/test/kotlin/BenchmarkJsonRoundTripTest.kt : benchmark.json write, read and merge round-trip tests
apps/benchmark/modules/benchmark/src/test/kotlin/CaseDocumentTest.kt : case document reader tests
apps/benchmark/modules/benchmark/src/test/kotlin/CaseSettingsTest.kt : HarnessSettings to CaseSettings tests
apps/benchmark/modules/benchmark/src/test/kotlin/EnergyCheckTest.kt : energy refusal and energyJ join tests
apps/benchmark/modules/benchmark/src/test/kotlin/EnergyRunTest.kt : CaseRuns composition tests
apps/benchmark/modules/benchmark/src/test/kotlin/HostHarnessTest.kt : host loop tests
apps/benchmark/modules/benchmark/src/test/kotlin/JetpackResultsTest.kt : Jetpack conversion tests over example/
apps/benchmark/modules/benchmark/src/test/kotlin/MergeTest.kt : per-process merge tests
apps/benchmark/modules/benchmark/src/test/kotlin/PlanCheckTest.kt : refusal tests
apps/benchmark/modules/benchmark/src/test/kotlin/RunCountAuditTest.kt : run-count audit tests
```
