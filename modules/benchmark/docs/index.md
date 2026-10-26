# benchmark

```
modules/benchmark/.gitignore : ignores /build
modules/benchmark/README.md : module summary and link to this index
modules/benchmark/build.gradle : Kotlin/JVM 17 library; api :preparation; snakeyaml 2.3; passes examples.update to tests
modules/benchmark/docs/index.md : this map
modules/benchmark/docs/measure.md : plan check, host harness, benchmark.json, merge, Jetpack conversion
modules/benchmark/example/benchmark_jetpack_example.json : example androidx benchmarkData.json
modules/benchmark/example/benchmark_prepared_example.yaml : prepared.yaml paired with the Jetpack example
modules/benchmark/src/main/kotlin/Benchmark.kt : runs PlanCheck, then measures unrefused cases
modules/benchmark/src/main/kotlin/RefusedPlanException.kt : default refusal handler's exception
modules/benchmark/src/main/kotlin/check/EnergyCapability.kt : parses energy.yaml; derives the energy refusal
modules/benchmark/src/main/kotlin/check/PlanCheck.kt : pre-timer refusals for a PreparedRun
modules/benchmark/src/main/kotlin/check/Refusal.kt : one refusal (caseId, reason)
modules/benchmark/src/main/kotlin/report/BenchmarkJson.kt : writes benchmark.json text
modules/benchmark/src/main/kotlin/report/CaseDocument.kt : shared YAML and JSON reader for case documents
modules/benchmark/src/main/kotlin/report/Merge.kt : merges per-process benchmark.json texts
modules/benchmark/src/main/kotlin/report/MetricSamples.kt : one metric's runs, iteration count, reported stats; metric key names
modules/benchmark/src/main/kotlin/report/ReportedStats.kt : androidx minimum, maximum, median, CoV for one process
modules/benchmark/src/main/kotlin/report/ResultRow.kt : one case row of benchmark.json
modules/benchmark/src/main/kotlin/report/energy/EnergyWindows.kt : reads energy.json into energyJ samples and invalid reasons
modules/benchmark/src/main/kotlin/report/jetpack/JetpackResults.kt : benchmarkData.json and prepared.yaml to rows and runtime
modules/benchmark/src/main/kotlin/report/jetpack/RunCountAudit.kt : compares requested iterations and allocation runs to actual runs
modules/benchmark/src/main/kotlin/run/BlackHole.kt : result sink
modules/benchmark/src/main/kotlin/run/CaseMeasurement.kt : one host-measured case: timeNs samples, median
modules/benchmark/src/main/kotlin/run/CaseSettings.kt : harness settings as plain values, no androidx type
modules/benchmark/src/main/kotlin/run/HostHarness.kt : host JVM timing loop
modules/benchmark/src/main/kotlin/run/TimedLoop.kt : calls once() until a nanosecond budget is spent; returns the call count
modules/benchmark/src/main/kotlin/run/compose/CaseRun.kt : fun interface run(): Long?
modules/benchmark/src/main/kotlin/run/compose/CaseRuns.kt : composes a CaseRun from the energy capture mode
modules/benchmark/src/main/kotlin/run/decorate/Cooldown.kt : sleeps after the inner run
modules/benchmark/src/main/kotlin/run/decorate/EnergyWindow.kt : brackets the inner run with an energy:<id> marker
modules/benchmark/src/main/kotlin/run/decorate/Rewarm.kt : TimedLoop warm-up before the inner run
modules/benchmark/src/main/kotlin/run/energy/Energy.kt : energy settings with defaults
modules/benchmark/src/main/kotlin/run/energy/WindowMarker.kt : begin and end marker port
modules/benchmark/src/test/kotlin/BenchmarkJsonRoundTripTest.kt : benchmark.json write, read and merge round-trip tests
modules/benchmark/src/test/kotlin/BlackHoleTest.kt : sink test
modules/benchmark/src/test/kotlin/CaseDocumentTest.kt : case document reader tests
modules/benchmark/src/test/kotlin/CaseSettingsTest.kt : HarnessSettings to CaseSettings tests
modules/benchmark/src/test/kotlin/EnergyCheckTest.kt : energy refusal and energyJ join tests
modules/benchmark/src/test/kotlin/EnergyRunTest.kt : CaseRuns composition tests
modules/benchmark/src/test/kotlin/HostHarnessTest.kt : host loop tests
modules/benchmark/src/test/kotlin/JetpackResultsTest.kt : Jetpack conversion tests over example/
modules/benchmark/src/test/kotlin/MergeTest.kt : per-process merge tests
modules/benchmark/src/test/kotlin/PlanCheckTest.kt : refusal tests
modules/benchmark/src/test/kotlin/RunCountAuditTest.kt : run-count audit tests
```
