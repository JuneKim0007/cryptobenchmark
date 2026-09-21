# <docs>

## documents

| Document | Holds |
|---|---|
| [README](../README.md) | scope, pipeline, requirements, how to run |
| `docs.md` | modules, file structure, language rule, dependency rules |
| [cryptography/primitives.md](cryptography/primitives.md) | primitive → provider → type catalogue, key sizes, usage rules |
| [cryptography/providers.md](cryptography/providers.md) | per-provider supported and unsupported algorithms |
| [infra/setup.md](infra/setup.md) | `:android` setup package |
| `modules/environment/discovery/docs/probe.md` | what `:environment:discovery` does, JCA APIs, limits, classes |
| `modules/environment/discovery/docs/security_contract.md` | capture and setting field tables |

## file structure

- gradle root is the repository root; modules live under `modules/`; package root in every module is `io.github.junekim0007.cryptobench`
  - `modules/crypto/` : module `:crypto` (android library) — cryptography, nothing else
    - `crypto/primitive/` : one algorithm call per function, no iteration, no lookup
      - `cipher/` : `EncryptOperation`, `DecryptOperation` — the two call shapes
        - `symmetric/` : AES, DESEDE, ChaCha20, ARC4 — encrypt, decrypt, `IvSpec`
        - `asymmetric/` : RSA — encrypt, decrypt
      - `digest/` : SHA family, MD5
      - `mac/` : HMAC
      - `signature/` : sign, verify
      - `keygen/` : secret keys, key pairs, signature keys
    - `crypto/codec/` : byte↔String, base64, charset
    - `src/test/` : JVM tests
  - `modules/environment/discovery/` : module `:environment:discovery` (kotlin, java library) — what this device offers, never inside a measurement
    - `README.md`, `docs/probe.md`, `docs/security_contract.md` : module docs
    - `src/main/kotlin/` : sub-package folders only, no package root folders
      - `adapter/` : reads the JCA and parses it into the contract — `ProviderProbe`, `PropertyMapIndex`, `PropertyKeyParser`, `PropertyKey`, `DeclaredAlias`, `AttributeKind`, `AttributeValueParser`, `DeviceRuntimeReader`
      - `contract/` : the captured model — `CapturedEnvironment`, `ProviderEntry`, `ServiceEntry`, `AliasEntry`, `ServiceAttributes`, `RuntimeInfo`, `ServiceKey`
      - `setting/` : `DiscoverySettingConverter` → `DiscoverySetting`, the capture reduced to `BenchmarkScope`; `ProviderSetting`, `ServiceSetting`, `Device`, `ServiceLookup`
      - `write/` : `CaptureDocument` (schema, `of` ⇄ `parse`) → `EnvironmentYamlWriter` → `probe_<utc>.yaml`; `ProviderClassNameWriter` → `probe_classes_<utc>.yaml`; `DocumentFields`, `YamlDocument`, `ProbeFile`
  - `modules/benchmark/` : module `:benchmark` (java library) — what is measured; standalone, not android-specific
    - `benchmark/preparation/` : turns what the user asked for into runnable state
      - `case/` : one measurement described — op, algorithm, mode, padding, provider, key size, input size *(planned)*
      - `registry/` : case registry *(planned — provider lookup is `DiscoverySetting.providersFor` for now)*
      - `key/` : key per case *(planned)*
      - `workload/` : `DataType`, `StringType` — input generation
  - `modules/android/` : module `:android` (application) — depends on all modules
    - `setup/config/` : `Config` — run parameters read from the pushed config
    - `src/androidTest/` : on-device benchmarks and functional tests
    - `src/test/` : JVM tests
    - `src/main/res/raw/` : `device_primitives.json` (old capture), `restrictions.json` (policy) — kept as data
  - `gradle.properties` : gradle env + signing + benchmark defaults
- `scripts/` : host side
  - `run_benchmarks.sh` : the sweep; entry point
  - `benchmark.py` : one run — build, install, push config, instrument, collect
  - `analyze_results.py` : validate results against logcat
- `docs/`
  - `docs.md` : this file
  - `cryptography/primitives.md` : primitives, providers, use
  - `cryptography/providers.md` : per-provider support and scope
  - `infra/setup.md` : setup
- `results/` : run output, ignored; one subdirectory per pipeline stage
  - `discovery/` : `probe_<utc>.yaml`, `probe_classes_<utc>.yaml`
  - `preparation/`, `benchmark/`, `analysis/` : *(planned)*
- `CryptoBenchmark.config` : generated per run, pushed to the device
- `scripts/requirements.txt` : host python deps
- `docs/notas.md` : research notes

### language

| Module | Language | Inside a measurement |
|---|---|---|
| `:crypto` | Java | yes — it is the subject |
| `:benchmark` | Java | prepares before the timed block, calls `:crypto` |
| `:android` | Java | hosts the measurement classes in `androidTest` |
| `:environment:discovery` | Kotlin | no — runs before any measurement |

Rules:

- Kotlin only where nothing is measured.
- Measured code moves to Kotlin only after a control measurement — same primitive, both
  languages, smallest input.
- Kotlin sources omit the package root folders under `src/main/kotlin/`; Java sources mirror
  the full package as folders under `src/main/java/`.
- A directory holding more than four files of the same kind gets sub-directories.

### phases

1. `discovery/` : determine device, runtime, hardware capability, benchmark compatibility
2. `setup/` : user config and user-supplied inputs (device state is Jetpack's, via runner args)
3. `benchmark/preparation/` : algorithm, inputs, keys, parameters for one case

### dependency rules

Enforced by gradle module dependencies:

| module | may depend on |
|---|---|
| `:crypto` | — |
| `:environment:discovery` | — |
| `:benchmark` | `:crypto`, `:environment:discovery` (none declared yet) |
| `:android` | all |

Inside `:android`:

- `setup` : imports `discovery`
- `androidTest` : imports `benchmark`, `crypto`
