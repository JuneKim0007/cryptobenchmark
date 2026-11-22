# Architecture

## Stage flow

```
config/benchmark/global.yaml + config/benchmark/testsets/*.yaml
        │
:environment:discovery ──probe_<stamp>.yaml, trial_<stamp>.yaml, requirements_<stamp>.yaml──▶ :config
:config ──inventory.yaml, effective.yaml──▶ :preparation
:preparation ──prepared cases in process; prepared.yaml, skipped.yaml on disk──▶ :benchmark
:benchmark ──benchmark.json──▶ apps/benchmark-runner/analysis/analyze.py ──summary.md, charts
```

| stage | reads | writes | code |
|---|---|---|---|
| discovery | JCA providers of the running JVM or device | `probe_<stamp>.yaml`, `trial_<stamp>.yaml`, `requirements_<stamp>.yaml` | `apps/benchmark/modules/environment/discovery/src/main/kotlin/write/`; schemas in `apps/benchmark/modules/environment/contract/src/main/kotlin/` |
| config | capture, trial, `global.yaml`, test set, optional `facts.yaml` | `inventory.yaml`, `effective.yaml` | `apps/benchmark/modules/config/src/main/kotlin/Configuration.kt` |
| preparation | capture, trial, `effective.yaml` | `prepared.yaml`, `skipped.yaml` | `apps/benchmark/modules/preparation/src/main/kotlin/record/PreparedFile.kt`, `report/SkipFile.kt`, written by benchmark's `check/RunnablePlan.kt` |
| benchmark | prepared cases, `energy.yaml` | `benchmark.json` | `apps/benchmark/modules/benchmark/src/main/kotlin/report/BenchmarkJson.kt` |
| analysis | `benchmark.json` | `summary.md`, `throughput.png`, `latency.png`, `stability.png`, `<metric>-vs-time.png` | `apps/benchmark-runner/analysis/analyze.py` |

- Stamp format: `yyyyMMdd'T'HHmmss'Z'`, UTC.
- `:config` reads capture and trial by key names; no discovery class is on its classpath.
- No provider, algorithm or device name is hard-coded in module main code; selection comes from `config/`.
- One command for both sides: `apps/cli/facade.py`, see [facade.md](facade.md): crypto (the benchmark) names nothing of the llm side (perf-repair) and the reverse; the root settings index names both.
- Driver: `apps/benchmark-runner/pipeline.py`, see [run.md](run.md). Output layout: [results.md](results.md).

## Gradle projects

| project | directory | project dependencies | libraries |
|---|---|---|---|
| `:files` | `apps/benchmark/modules/files` | none | none |
| `:jca` | `apps/benchmark/modules/jca` | none | none |
| `:document` | `apps/benchmark/modules/document` | none | snakeyaml 2.3 |
| `:environment:contract` | `apps/benchmark/modules/environment/contract` | `implementation :files`, `implementation :document` | none |
| `:environment:discovery` | `apps/benchmark/modules/environment/discovery` | `api :jca`, `api :environment:contract`, `implementation :files`, `implementation :document` | none |
| `:settings` | `apps/benchmark/modules/settings` | none | none |
| `:records` | `apps/benchmark/modules/records` | `implementation :document` | none |
| `:catalogue` | `apps/benchmark/modules/catalogue` | `api :files` | none |
| `:config` | `apps/benchmark/modules/config` | `implementation :settings`, `implementation :records`, `implementation :catalogue`, `implementation :files`, `implementation :document` | snakeyaml 2.3 |
| `:preparation` | `apps/benchmark/modules/preparation` | `api :settings`, `api :records`, `api :catalogue`, `api :jca`, `implementation :files`, `implementation :document` | snakeyaml 2.3 |
| `:benchmark` | `apps/benchmark/modules/benchmark` | `api :preparation`, `implementation :files`, `implementation :document` | snakeyaml 2.3 |
| `:android` | `apps/benchmark/modules/android` | `androidTestImplementation :benchmark`, `:environment:discovery`, `:files`, `:document` | benchmark-junit4 1.5.0; androidTest: androidx.test:runner 1.5.2, junit 4.13.2 |

- JVM modules test with junit 4.13.2.
- The SnakeYAML version is declared once, in `apps/benchmark/gradle/libs.versions.toml`; the cli and tools/ builds import it in their settings.

- `apps/benchmark/settings.gradle` includes the eleven projects; `rootProject.name = cryptobenchmark`.
- Package root: `io.github.junekim0007.cryptobench`.
- Root buildscript pins AGP 8.13.2 and Kotlin plugin 2.2.21.
- One wrapper, `apps/benchmark/gradlew`: Gradle 9.5.1.
- `apps/benchmark/gradle.properties`: `org.gradle.jvmargs=-Xmx2048m`, `android.useAndroidX=true`, `android.enableJetifier=true`.
- JVM modules target Java 17.
- `:android`: compileSdk 36, minSdk 26, targetSdk 36, runner `androidx.benchmark.junit4.AndroidBenchmarkRunner`, testBuildType release, release signed with the debug key, NDK 29.0.14206865, CMake 3.22.1.
- Instrumentation harness: `apps/benchmark/modules/android/docs/harness.md`.

## Languages

| project | languages | source layout |
|---|---|---|
| `:document`, `:environment:contract`, `:environment:discovery`, `:settings`, `:records`, `:catalogue`, `:config`, `:preparation`, `:benchmark` | Kotlin | `src/main/kotlin/`, package root folders omitted |
| `:android` | Kotlin main (`Affinity.kt`), C (`src/main/cpp/affinity.c`, `CMakeLists.txt`), Kotlin androidTest | full package folders |
| `apps/benchmark-runner/` | Python 3 | the entry points `pipeline.py`, `dependencies.py`, `explain.py` and their error line `failure.py`; every other module they import is in `lib/cryptobench` (`tools/tests/test_runner_layout.py`) |
| `lib/cryptobench/cryptobench/` | Python 3 | `shared/` components, `pipeline/` the stage framework, `stages/<stage>/` one package per stage: configuration, discovery, measurement, analysis, verification |
| `apps/benchmark-runner/energy/`, `apps/benchmark-runner/analysis/*.py` | Python 3 | flat |

- No `.java` source is tracked under `apps/benchmark/modules/`.
- A stage imports no other stage and `shared/` imports no stage; the routes in `pipeline.py` compose the stages, passing a step in where it runs inside another stage's staging or rollback (`tools/tests/test_lib_layers.py`).

## Example files

- `apps/benchmark/modules/<m>/example/<module>_<responsibility>_example.(yaml|json)` exist for config, preparation, benchmark.
- `:settings`, `:records` and `:catalogue` have no `example/`.

## Isolation build

`tools/module-isolation` builds each module from its own sources.

| subproject | compiled sources | libraries |
|---|---|---|
| `files` | `apps/benchmark/modules/files/src/main/kotlin` | junit 4.13.2 (test) |
| `document` | `apps/benchmark/modules/document/src/main/kotlin` | snakeyaml 2.3; junit 4.13.2 (test) |
| `contract` | `apps/benchmark/modules/environment/contract/src/main/kotlin` + `apps/benchmark/modules/files` + `apps/benchmark/modules/document` | snakeyaml 2.3 |
| `discovery` | `apps/benchmark/modules/environment/discovery/src/main/kotlin` + `apps/benchmark/modules/environment/contract` + `apps/benchmark/modules/files` + `apps/benchmark/modules/document` | snakeyaml 2.3; junit 4.13.2 (test) |
| `config` | `apps/benchmark/modules/config` + `apps/benchmark/modules/settings` + `apps/benchmark/modules/records` + `apps/benchmark/modules/catalogue` + `apps/benchmark/modules/files` + `apps/benchmark/modules/document` | same |
| `preparation` | `apps/benchmark/modules/preparation` + `apps/benchmark/modules/settings` + `apps/benchmark/modules/records` + `apps/benchmark/modules/catalogue` + `apps/benchmark/modules/files` + `apps/benchmark/modules/document` | same |
| `benchmark` | `apps/benchmark/modules/benchmark` + `apps/benchmark/modules/preparation` + `apps/benchmark/modules/settings` + `apps/benchmark/modules/records` + `apps/benchmark/modules/catalogue` + `apps/benchmark/modules/files` + `apps/benchmark/modules/document` | same |
| `architecture` | tests only: the module subprojects' compiled classes against `tools/module-isolation/layers.yaml` | archunit 1.5.1, snakeyaml 2.3, junit 4.13.2 (test) |

- `:settings`, `:records`, `:catalogue` and `:android` are not subprojects.
- guide resources (`apps/benchmark/gradle/guide-resources.gradle`): `algorithms/setup-catalog.yaml` at the classpath root, `setup-catalog.yaml` beside preparation's `operation/SetupCatalog` `engine-operations.yaml` beside its `engine/EngineTypes`, in every build that compiles config or preparation (root, isolation, cli); the seven family catalogues discovery and preparation read, `provider-builds.yaml`, `deviations.yaml` and `groups.yaml` beside document's `catalogue/FamilyCatalogue` and `algorithm-names.yaml` beside its `names/AlgorithmNames`, carried by `:document` alone in the root build (the APK merges module jars) and by each reading module in the isolation and cli builds.
- Tests run with `workingDir` = the module directory.
- `-Dexamples.update` is forwarded to tests.
- CI: `.github/workflows/modules.yml` runs `../../apps/benchmark/gradlew -p . :<m>:test` per subproject on Java 17.
- Commands: [tools.md](tools.md#module-isolation).

## Tools builds

- `apps/benchmark/cli` and each `tools/*` Gradle check are standalone Gradle projects that compile module sources by path.
- None is included in `apps/benchmark/settings.gradle`.
- Pipeline and CI run each of them through `apps/benchmark/gradlew -p <dir>`.
