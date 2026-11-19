# settings

```
apps/benchmark/modules/settings/.gitignore : ignores /build
apps/benchmark/modules/settings/README.md : module summary and link to this index
apps/benchmark/modules/settings/build.gradle : Kotlin/JVM 17 library; depends on :files only
apps/benchmark/modules/settings/docs/index.md : this map
apps/benchmark/modules/settings/docs/settings.md : harness key table, validation, merge, device support
apps/benchmark/modules/settings/src/main/kotlin/CpuSettings.kt : CpuSettings, its cpu key table and device support
apps/benchmark/modules/settings/src/main/kotlin/EnergySettings.kt : EnergySettings, its energy key table, the capture modes and the sources
apps/benchmark/modules/settings/src/main/kotlin/EngineRows.kt : setup-catalog.yaml's rows: the paths a type applies (none without a row: not_in_catalogue), the key generators
apps/benchmark/modules/settings/src/main/kotlin/Facts.kt : device facts read from facts.yaml
apps/benchmark/modules/settings/src/main/kotlin/Harness.kt : HarnessSettings and the harness key table
apps/benchmark/modules/settings/src/main/kotlin/Key.kt : Key, Leaf and Nested setting definitions
apps/benchmark/modules/settings/src/main/kotlin/Metric.kt : run.metrics enum TIME, ALLOCATION; reading
apps/benchmark/modules/settings/src/main/kotlin/OnFailure.kt : policy.onFailure: STOP, SKIP; config and preparation read it
apps/benchmark/modules/settings/src/main/kotlin/Phase.kt : run.phases enum WARM; reading (unknown_phase, duplicate)
apps/benchmark/modules/settings/src/main/kotlin/RunKeys.kt : the effective run section's keys: config writes them, preparation accepts them, Python's RUN_KEYS agrees
apps/benchmark/modules/settings/src/main/kotlin/Section.kt : ordered key table: read, write, merge, forDevice
apps/benchmark/modules/settings/src/main/kotlin/Skip.kt : one skipped item {stage, provider?, type?, name?, caseId?, code, reason}, its record map and read; report.yaml and skipped.yaml list them
apps/benchmark/modules/settings/src/main/kotlin/StoppedOnFailureException.kt : thrown under onFailure stop, carrying every skip
apps/benchmark/modules/settings/src/main/kotlin/Support.kt : Support and Unsupported
apps/benchmark/modules/settings/src/main/kotlin/Values.kt : single-value type readers
apps/benchmark/modules/settings/src/test/kotlin/EngineRowsTest.kt : catalogue rows: paths, a missing type, invalid variants, one generator per key kind
apps/benchmark/modules/settings/src/test/kotlin/SettingsTest.kt : settings tests
```
