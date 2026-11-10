# settings

```
apps/benchmark/modules/settings/.gitignore : ignores /build
apps/benchmark/modules/settings/README.md : module summary and link to this index
apps/benchmark/modules/settings/build.gradle : Kotlin/JVM 17 library; no project or library dependency
apps/benchmark/modules/settings/docs/index.md : this map
apps/benchmark/modules/settings/docs/settings.md : harness key table, validation, merge, device support
apps/benchmark/modules/settings/src/main/kotlin/CpuSettings.kt : CpuSettings, its cpu key table and device support
apps/benchmark/modules/settings/src/main/kotlin/EnergySettings.kt : EnergySettings, its energy key table, the capture modes and the sources
apps/benchmark/modules/settings/src/main/kotlin/Facts.kt : device facts read from facts.yaml
apps/benchmark/modules/settings/src/main/kotlin/Harness.kt : HarnessSettings and the harness key table
apps/benchmark/modules/settings/src/main/kotlin/Key.kt : Key, Leaf and Nested setting definitions
apps/benchmark/modules/settings/src/main/kotlin/Metric.kt : run.metrics enum TIME, ALLOCATION; reading
apps/benchmark/modules/settings/src/main/kotlin/Section.kt : ordered key table: read, write, merge, forDevice
apps/benchmark/modules/settings/src/main/kotlin/Support.kt : Support and Unsupported
apps/benchmark/modules/settings/src/main/kotlin/Values.kt : single-value type readers
apps/benchmark/modules/settings/src/test/kotlin/SettingsTest.kt : settings tests
```
