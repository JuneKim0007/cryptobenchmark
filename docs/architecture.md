# Architecture

## Stage flow

```
config/global.yaml + config/testsets/*.yaml
        │
:environment:discovery ──probe_<stamp>.yaml, trial_<stamp>.yaml, requirements_<stamp>.yaml──▶ :config
:config ──inventory.yaml, effective.yaml──▶ :preparation
:preparation ──prepared cases in process; prepared.yaml, skipped.yaml on disk──▶ :benchmark
:benchmark ──benchmark.json──▶ apps/benchmark-runner/analysis/analyze.py ──summary.md, charts
```

| stage | reads | writes | code |
|---|---|---|---|
| discovery | JCA providers of the running JVM or device | `probe_<stamp>.yaml`, `trial_<stamp>.yaml`, `requirements_<stamp>.yaml` | `apps/benchmark/modules/environment/discovery/src/main/kotlin/write/` |
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
| `:jca` | `apps/benchmark/modules/jca` | none | none |
| `:environment:discovery` | `apps/benchmark/modules/environment/discovery` | `api :jca` | snakeyaml 2.3 |
| `:settings` | `apps/benchmark/modules/settings` | none | none |
| `:config` | `apps/benchmark/modules/config` | `implementation :settings` | snakeyaml 2.3 |
| `:preparation` | `apps/benchmark/modules/preparation` | `api :settings`, `api :jca` | snakeyaml 2.3 |
| `:benchmark` | `apps/benchmark/modules/benchmark` | `api :preparation` | snakeyaml 2.3 |
| `:android` | `apps/benchmark/modules/android` | `androidTestImplementation :benchmark`, `:environment:discovery` | benchmark-junit4 1.5.0; androidTest: androidx.test:runner 1.5.2, junit 4.13.2 |

- JVM modules test with junit 4.13.2.

- `apps/benchmark/settings.gradle` includes the six projects; `rootProject.name = cryptobenchmark`.
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
| `:environment:discovery`, `:settings`, `:config`, `:preparation`, `:benchmark` | Kotlin | `src/main/kotlin/`, package root folders omitted |
| `:android` | Kotlin main (`Affinity.kt`), C (`src/main/cpp/affinity.c`, `CMakeLists.txt`), Kotlin androidTest | full package folders |
| `apps/benchmark-runner/` | Python 3 | commands and shared steps at the top; the other modules in one package per stage, imported with `apps/benchmark-runner/` on the path |
| `apps/benchmark-runner/energy/`, `apps/benchmark-runner/analysis/*.py` | Python 3 | flat |
| `apps/benchmark-runner/demo.sh` | bash | |

- No `.java` source is tracked under `apps/benchmark/modules/`.

## Example files

- `apps/benchmark/modules/<m>/example/<module>_<responsibility>_example.(yaml|json)` exist for discovery, config, preparation, benchmark.
- `:settings` has no `example/`.

## Isolation build

`tools/module-isolation` builds each module from its own sources.

| subproject | compiled sources | libraries |
|---|---|---|
| `discovery` | `apps/benchmark/modules/environment/discovery/src/main/kotlin` | snakeyaml 2.3; junit 4.13.2 (test) |
| `config` | `apps/benchmark/modules/config` + `apps/benchmark/modules/settings` | same |
| `preparation` | `apps/benchmark/modules/preparation` + `apps/benchmark/modules/settings` | same |
| `benchmark` | `apps/benchmark/modules/benchmark` + `apps/benchmark/modules/preparation` + `apps/benchmark/modules/settings` | same |
| `architecture` | tests only: the four subprojects' compiled classes against `tools/module-isolation/layers.yaml` | archunit 1.5.1, snakeyaml 2.3, junit 4.13.2 (test) |

- `:settings` and `:android` are not subprojects.
- `config` resources: `algorithms/algorithm-names.yaml`, on the classpath of every build that compiles `apps/benchmark/modules/config` (root, isolation, cli); perf-repair packages a copy its tests compare with it.
- Tests run with `workingDir` = the module directory.
- `-Dexamples.update` is forwarded to tests.
- CI: `.github/workflows/modules.yml` runs `../../apps/benchmark/gradlew -p . :<m>:test` per subproject on Java 17.
- Commands: [tools.md](tools.md#module-isolation).

## Tools builds

- `apps/benchmark/cli` and each `tools/*` Gradle check are standalone Gradle projects that compile module sources by path.
- None is included in `apps/benchmark/settings.gradle`.
- Pipeline, demo and CI run each of them through `apps/benchmark/gradlew -p <dir>`.
