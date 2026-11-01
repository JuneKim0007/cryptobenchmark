# settings

```
modules/settings/.gitignore : ignores /build
modules/settings/README.md : module summary and link to this index
modules/settings/build.gradle : Kotlin/JVM 17 library; no project or library dependency
modules/settings/docs/index.md : this map
modules/settings/docs/settings.md : harness key table, validation, merge, device support
modules/settings/src/main/kotlin/Facts.kt : device facts read from facts.yaml
modules/settings/src/main/kotlin/Harness.kt : HarnessSettings, EnergySettings, CpuSettings and their key tables
modules/settings/src/main/kotlin/Key.kt : Key, Leaf and Nested setting definitions
modules/settings/src/main/kotlin/Metric.kt : run.metrics enum TIME, ALLOCATION, CPU_EVENTS; reading and device support
modules/settings/src/main/kotlin/Section.kt : ordered key table: read, write, merge, forDevice
modules/settings/src/main/kotlin/Support.kt : Support and Unsupported
modules/settings/src/main/kotlin/Values.kt : single-value type readers
modules/settings/src/test/kotlin/SettingsTest.kt : settings tests
```
