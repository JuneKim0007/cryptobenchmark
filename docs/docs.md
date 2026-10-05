# docs

## documents

| Document | Holds |
|---|---|
| [README](../README.md) | scope, pipeline, requirements, how to run |
| `docs.md` | modules, file structure, language rule, dependency rules |
| [cryptography/primitives.md](cryptography/primitives.md) | primitive → provider → type catalogue, key sizes, usage rules |
| [cryptography/providers.md](cryptography/providers.md) | per-provider supported and unsupported algorithms |
| `modules/config/docs/config.md` | authored and generated config files, fields, precedence |
| `modules/preparation/docs/prepare.md` | `effective.yaml` → cases: axes, parameter trees, failures |
| `modules/benchmark/docs/measure.md` | cases → measurements: what one sample is, refusals, the device run |
| `modules/environment/discovery/docs/probe.md` | what `:environment:discovery` does, JCA APIs, limits, classes |
| `modules/environment/discovery/docs/security_contract.md` | capture and trial field tables |
| `tools/module-isolation/README.md`, `tools/quick-bench/README.md` | the isolation build; the JVM stand-in harness |

## file structure

- gradle root is the repository root; modules live under `modules/`; package root in every module is `io.github.junekim0007.cryptobench`
  - `config/` : authored, committed — `global.yaml` (test set, input sizes, seed, iterations), `global.reference.yaml` (every key), `global-{quick,demo}.yaml`, `testsets/{scope,quick,all,smoke}.yaml`
  - `modules/environment/discovery/` : module `:environment:discovery` (kotlin) — what this device offers
  - `modules/config/` : module `:config` (kotlin) — capture × trial × authored config → `effective.yaml`
  - `modules/preparation/` : module `:preparation` (kotlin) — `effective.yaml` + capture + trial → prepared cases
  - `modules/benchmark/` : module `:benchmark` (kotlin) — prepared cases → measurements; built with `:preparation`
  - `modules/*/example/` : one small device in the files that module reads and writes, `<module>_<responsibility>_example.yaml`
  - `modules/android/` : module `:android` (application) — the instrumentation target; `src/androidTest/` holds the Jetpack harness
  - `gradle.properties` : gradle env + signing
- `scripts/`
  - `pipeline.py` : the host driver — stages in order, one readable failure; `--config`, `--results`, `--discovery overwrite|keep|reuse`, `--bench`, `--stream`
  - `effective_view.py`, `gradle_runner.py`, `failure.py` : what `pipeline.py` and `explain.py` share — reading `effective.yaml` with its report, running a gradle tool, stopping with one message
  - `explain.py` : prints the settings a run resolved to and where each came from (the global file or a default); `--config`, `--results`
  - `demo.sh` : one live run into `results/demo/`; `--warm`, `--fast`, `--reuse`
  - `requirements.txt` : host python deps
- `tools/`
  - `jca-contract/` : the host command (probe → trial → inventory → effective) and the JCA contract tests
  - `android-api-check/` : compiles `discovery`, `preparation` and `benchmark` against `android.jar` with no JDK on the classpath
  - `quick-bench/` : the host driver for `:benchmark` (`BenchKt`, `ConvertKt`, `MergeRunsKt`), the analysis script, `charts.py` with its `chart_*.py` parts (IQR bars, `summary.md`, `chart-data.json`, `manifest.yaml` under `results/chart/<run-id>/`) and `stats.py` (the statistics, one definition each)
  - `module-isolation/` : compiles each module alone and runs it against its `example/` files
- `docs/`
  - `docs.md` : this file
  - `cryptography/primitives.md`, `cryptography/providers.md` : catalogue
- `results/` : run output, ignored
  - `discovery/` : `probe_<utc>.yaml`, `probe_classes_<utc>.yaml`, `trial_<utc>.yaml`
  - `configuration/` : `inventory.yaml`, `effective.yaml`, `report.yaml`
  - `preparation/` : `prepared.yaml`, `skipped.yaml`
  - `chart/<run-id>/` : `summary.md`, `chart-data.json`, `manifest.yaml`, and `<n>-<group>/iqr-bars_<op>_input-<size>.png`; `analysis.dir` moves the root
  - `benchmark/` : `benchmark.json`, and `process-<n>/` when `processRepetitions` is more than one
  - `analysis/` : `summary.md` and three charts, from `analyze.py` (the older script)

Each module's own README lists its files and responsibilities.

### language

| Module | Language | Inside a measurement |
|---|---|---|
| `:preparation` | Kotlin | no — prepares before the timed block |
| `:benchmark` | Kotlin | yes — it is the timed run; the call it times is built before the timer |
| `:android` | Kotlin, `androidTest` only | yes — `BenchmarkRule` over the same call |
| `:environment:discovery` | Kotlin | no — runs before any measurement |
| `:config` | Kotlin | no — files only |

Rules:

- Kotlin only where nothing is measured.
- Measured code moves to Kotlin only after a control measurement — same primitive, both
  languages, smallest input.
- Kotlin sources omit the package root folders under `src/main/kotlin/`; Java sources mirror
  the full package as folders under `src/main/java/`.
- A directory holding more than four files of the same kind gets sub-directories.

### phases

1. `environment/` : providers, services, aliases, attributes; what instantiates and what runs with a default key
2. `configuration/` : inventory × authored `config/` → the effective set for one run
3. `preparation/` : operations, keys, inputs and parameters per case; each case called once
4. `benchmark/` : refuse what this device cannot run, then time each case
5. `analysis/`, `chart/` : medians, spread, stability and IQR charts per group; `analysis.charts` in the global file picks them

### dependency rules

Enforced by gradle module dependencies:

| module | may depend on |
|---|---|
| `:environment:discovery` | — |
| `:config` | — reads the capture and trial files, not `:environment:discovery` classes |
| `:preparation` | — reads the capture, the trial and `effective.yaml`, not another module's classes |
| `:benchmark` | `:preparation` — the one project dependency: it times the `Invocation` preparation builds |
| `:android` | `:benchmark`, in `androidTest` only — it has no main sources |

Only `:benchmark` declares a project dependency. `tools/module-isolation` compiles each module with
only snakeyaml and JUnit on the classpath — `benchmark` with `preparation` beside it — so a reach
across any other pair fails the build, and CI runs the four as a matrix.

`tools/` builds are separate Gradle projects; they read module sources directly and ship nothing.
