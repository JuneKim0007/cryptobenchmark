# <docs>

## documents

| Document | Holds |
|---|---|
| [README](../README.md) | scope, pipeline, requirements, how to run |
| `docs.md` | modules, file structure, language rule, dependency rules |
| [cryptography/primitives.md](cryptography/primitives.md) | primitive → provider → type catalogue, key sizes, usage rules |
| [cryptography/providers.md](cryptography/providers.md) | per-provider supported and unsupported algorithms |
| `modules/config/docs/config.md` | authored and generated config files, fields, precedence |
| `modules/preparation/docs/prepare.md` | `effective.yaml` → cases: axes, parameter trees, failures |
| `modules/environment/discovery/docs/probe.md` | what `:environment:discovery` does, JCA APIs, limits, classes |
| `modules/environment/discovery/docs/security_contract.md` | capture and setting field tables |

## file structure

- gradle root is the repository root; modules live under `modules/`; package root in every module is `io.github.junekim0007.cryptobench`
  - `config/` : authored, committed — `global.yaml` (selection, run, policy), `testsets/{scope,quick,all,smoke}.yaml`
  - `modules/crypto/` : module `:crypto` (android library) — the primitives being measured
    - `crypto/primitive/` : one algorithm call per function — `cipher/`, `digest/`, `mac/`, `signature/`, `keygen/`
    - `crypto/codec/` : byte↔String, base64, charset
  - `modules/environment/discovery/` : module `:environment:discovery` (kotlin) — what this device offers
  - `modules/config/` : module `:config` (kotlin) — inventory × authored config → `effective.yaml`
  - `modules/preparation/` : module `:preparation` (kotlin) — `effective.yaml` → prepared cases
  - `modules/android/` : module `:android` (application) — app shell; the harness lands here with #33
  - `gradle.properties` : gradle env + signing
- `scripts/`
  - `pipeline.py` : the host driver — runs the stages in order, one readable failure, `--config`, `--results`, `--discovery overwrite|keep|reuse`, `--bench`
  - `requirements.txt` : host python deps
- `tools/`
  - `jca-contract/` : the host command (probe → trial → inventory → effective) and the JCA contract tests
  - `android-api-check/` : compiles the on-device modules against `android.jar` without the JDK
  - `quick-bench/` : JVM stand-in harness and analysis, until #33
- `docs/`
  - `docs.md` : this file
  - `cryptography/primitives.md`, `cryptography/providers.md` : catalogue
- `results/` : run output, ignored
  - `discovery/` : `probe_<utc>.yaml`, `probe_classes_<utc>.yaml`, `trial_<utc>.yaml`
  - `configuration/` : `inventory.yaml`, `effective.yaml`
  - `preparation/` : `skipped.yaml`
  - `benchmark/`, `analysis/` : quick-bench output; Jetpack output lands here with #33

Each module's own README lists its files and responsibilities.

### language

| Module | Language | Inside a measurement |
|---|---|---|
| `:crypto` | Java | yes — it is the subject |
| `:preparation` | Kotlin | no — prepares before the timed block |
| `:benchmark` *(planned)* | as `:crypto` | yes — it is the timed run |
| `:android` | Java | app shell; hosts the harness with #33 |
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
4. `benchmark/` : the timed run *(planned, #33)*
5. `analysis/` : median, percentiles, stability, comparisons *(planned)*

### dependency rules

Enforced by gradle module dependencies:

| module | may depend on |
|---|---|
| `:crypto` | — |
| `:environment:discovery` | — |
| `:config` | — (reads environment's files, not its classes) |
| `:preparation` | `:environment:discovery` (declared, `api`; imported only by `adapter/`); reads `effective.yaml`, not `:config` classes |
| `:benchmark` *(planned)* | `:preparation`, `:crypto` |
| `:android` | all |

`tools/` builds are separate Gradle projects; they read module sources directly and ship nothing.
