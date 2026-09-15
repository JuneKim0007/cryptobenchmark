# <docs>

## documents

| Document | Holds |
|---|---|
| [README](../README.md) | scope, pipeline, requirements, how to run |
| `docs.md` | modules, file structure, language rule, dependency rules |
| [cryptography/primitives.md](cryptography/primitives.md) | primitive → provider → type catalogue, key sizes, usage rules |
| [cryptography/providers.md](cryptography/providers.md) | per-provider supported and unsupported algorithms |
| [infra/setup.md](infra/setup.md) | `:app` setup package |
| `android/discovery/probe.md` | what `:discovery` does, JCA APIs, limits, classes |
| `android/discovery/security_contract.md` | capture and setting field tables |

## file structure

- `android/` : gradle project; package root in every module is `io.github.junekim0007.cryptobench`
  - `crypto/` : module `:crypto` (android library) — cryptography, nothing else
    - `crypto/primitive/` : one algorithm call per function, no iteration, no lookup
      - `cipher/` : `EncryptOperation`, `DecryptOperation` — the two call shapes
        - `symmetric/` : AES, DESEDE, ChaCha20, ARC4 — encrypt, decrypt, keygen, `IvSpec`
        - `asymmetric/` : RSA — encrypt, decrypt, keygen
      - `digest/` : SHA family, MD5
      - `mac/` : HMAC
      - `signature/` : sign, verify, signature keygen
    - `crypto/codec/` : byte↔String, base64, charset
    - `src/test/` : JVM tests
  - `discovery/` : module `:discovery` (kotlin, java library) — what this device offers, never inside a measurement
    - `probe.md`, `security_contract.md` : module docs
    - `src/main/kotlin/` : flat, no package folders
      - `ProviderProbe` : reads the JCA into a capture
      - `CapturedEnvironment`, `ProviderEntry`, `ServiceEntry`, `ServiceAttributes`, `RuntimeInfo` : the capture model
      - `PropertyKey`, `ServiceKey`, `AttributeKind` : property-map classification and keys — `internal`
      - `EnvironmentJsonWriter` : capture → JSON
      - `DiscoverySettingConverter` → `DiscoverySetting` : capture reduced to what the benchmark needs
  - `benchmark/` : module `:benchmark` (java library; becomes the `androidx.benchmark` module at #11) — what is measured
    - `benchmark/preparation/` : turns what the user asked for into runnable state
      - `case/` : one measurement described — op, algorithm, mode, padding, provider, key size, input size *(planned)*
      - `registry/` : case registry *(planned — provider lookup is `DiscoverySetting.providersFor` for now)*
      - `key/` : key per case *(planned)*
      - `workload/` : `DataType`, `StringType` — input generation
  - `app/` : module `:app` (application) — depends on all modules
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
- `CryptoBenchmark.config` : generated per run, pushed to the device
- `requirements.txt` : host python deps
- `notas.md` : research notes

### language

| Module | Language | Inside a measurement |
|---|---|---|
| `:crypto` | Java | yes — it is the subject |
| `:benchmark` | Java | prepares before the timed block, calls `:crypto` |
| `:app` | Java | hosts the measurement classes in `androidTest` |
| `:discovery` | Kotlin | no — runs before any measurement |

Rules:

- Kotlin only where nothing is measured.
- Measured code moves to Kotlin only after a control measurement — same primitive, both
  languages, smallest input.
- Kotlin sources are flat under `src/main/kotlin/`; Java sources mirror the package as
  folders under `src/main/java/`.

### phases

1. `discovery/` : determine device, runtime, hardware capability, benchmark compatibility
2. `setup/` : user config and user-supplied inputs (device state is Jetpack's, via runner args)
3. `benchmark/preparation/` : algorithm, inputs, keys, parameters for one case

### dependency rules

Enforced by gradle module dependencies:

| module | may depend on |
|---|---|
| `:crypto` | — |
| `:discovery` | — |
| `:benchmark` | `:crypto`, `:discovery` (none declared yet) |
| `:app` | all |

Inside `:app`:

- `setup` : imports `discovery`
- `androidTest` : imports `benchmark`, `crypto`
