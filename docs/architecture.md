# Architecture

## Stage flow

```
config/global.yaml + config/testsets/*.yaml
        │
:environment:discovery ──probe_<stamp>.yaml, probe_classes_<stamp>.yaml, trial_<stamp>.yaml──▶ :config
:config ──inventory.yaml, effective.yaml──▶ :preparation
:preparation ──prepared cases in process; prepared.yaml, skipped.yaml on disk──▶ :benchmark
:benchmark ──benchmark.json──▶ tools/quick-bench/analyze.py ──summary.md, charts
```

| stage | reads | writes | code |
|---|---|---|---|
| discovery | JCA providers of the running JVM or device | `probe_<stamp>.yaml`, `probe_classes_<stamp>.yaml`, `trial_<stamp>.yaml` | `modules/environment/discovery/src/main/kotlin/write/` |
| config | capture, trial, `global.yaml`, test set, optional `facts.yaml` | `inventory.yaml`, `effective.yaml` | `modules/config/src/main/kotlin/Configuration.kt` |
| preparation | capture, trial, `effective.yaml` | `prepared.yaml`, `skipped.yaml` | `modules/preparation/src/main/kotlin/record/PreparedFile.kt`, `report/SkipFile.kt` |
| benchmark | prepared cases, `energy.yaml` | `benchmark.json` | `modules/benchmark/src/main/kotlin/report/BenchmarkJson.kt` |
| analysis | `benchmark.json` | `summary.md`, three PNG charts | `tools/quick-bench/analyze.py` |

- Stamp format: `yyyyMMdd'T'HHmmss'Z'`, UTC.
- `:config` reads capture and trial by key names; no discovery class is on its classpath.
- No provider, algorithm or device name is hard-coded in module main code; selection comes from `config/`.
- Driver: `scripts/pipeline.py`, see [run.md](run.md). Output layout: [results.md](results.md).

## Gradle projects

| project | directory | project dependencies | libraries |
|---|---|---|---|
| `:environment:discovery` | `modules/environment/discovery` | none | snakeyaml 2.3 |
| `:settings` | `modules/settings` | none | none |
| `:config` | `modules/config` | `implementation :settings` | snakeyaml 2.3 |
| `:preparation` | `modules/preparation` | `api :settings` | snakeyaml 2.3 |
| `:benchmark` | `modules/benchmark` | `api :preparation` | snakeyaml 2.3 |
| `:android` | `modules/android` | `androidTestImplementation :benchmark`, `:environment:discovery` | benchmark-junit4 1.5.0; androidTest: androidx.test:runner 1.5.2, junit 4.13.2 |

- JVM modules test with junit 4.13.2.

- `settings.gradle` includes the six projects; `rootProject.name = cryptobenchmark`.
- Package root: `io.github.junekim0007.cryptobench`.
- Root buildscript pins AGP 8.13.2 and Kotlin plugin 2.2.21.
- Root wrapper: Gradle 9.5.1. `tools/` wrapper: Gradle 9.6.1.
- `gradle.properties`: `org.gradle.jvmargs=-Xmx2048m`, `android.useAndroidX=true`, `android.enableJetifier=true`.
- JVM modules target Java 17.
- `:android`: compileSdk 36, minSdk 26, targetSdk 36, runner `androidx.benchmark.junit4.AndroidBenchmarkRunner`, testBuildType release, release signed with the debug key, NDK 29.0.14206865, CMake 3.22.1.
- Instrumentation harness: `modules/android/docs/harness.md`.

## Languages

| project | languages | source layout |
|---|---|---|
| `:environment:discovery`, `:settings`, `:config`, `:preparation`, `:benchmark` | Kotlin | `src/main/kotlin/`, package root folders omitted |
| `:android` | Kotlin main (`Affinity.kt`), C (`src/main/cpp/affinity.c`, `CMakeLists.txt`), Kotlin androidTest | full package folders |
| `scripts/`, `tools/energy/`, `tools/quick-bench/*.py` | Python 3 | flat |
| `scripts/demo.sh` | bash | |

- No `.java` source is tracked under `modules/`.

## Example files

- `modules/<m>/example/<module>_<responsibility>_example.(yaml|json)` exist for discovery, config, preparation, benchmark.
- `:settings` has no `example/`.

## Isolation build

`tools/module-isolation` builds each module from its own sources.

| subproject | compiled sources | libraries |
|---|---|---|
| `discovery` | `modules/environment/discovery/src/main/kotlin` | snakeyaml 2.3; junit 4.13.2 (test) |
| `config` | `modules/config` + `modules/settings` | same |
| `preparation` | `modules/preparation` + `modules/settings` | same |
| `benchmark` | `modules/benchmark` + `modules/preparation` + `modules/settings` | same |

- `:settings` and `:android` are not subprojects.
- `config` resources: `perf-repair/src/perfrepair/catalog/algorithm-names.yaml`, copied by every build that compiles `modules/config` (root, isolation, jca-contract).
- Tests run with `workingDir` = the module directory.
- `-Dexamples.update` is forwarded to tests.
- CI: `.github/workflows/modules.yml` runs `../jca-contract/gradlew -p . :<m>:test` per subproject on Java 17.
- Commands: [tools.md](tools.md#module-isolation).

## Tools builds

- Each `tools/*` build is a standalone Gradle project that compiles module sources by path.
- No `tools/*` build is included in `settings.gradle`.
- Pipeline, demo and CI run every `tools/` build through `tools/jca-contract/gradlew -p <dir>`.
