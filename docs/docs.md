# <docs>

## documents

| Document | Holds |
|---|---|
| [README](../README.md) | scope, pipeline, requirements, how to run |
| `docs.md` | modules, file structure, language rule, dependency rules |
| [cryptography/primitives.md](cryptography/primitives.md) | primitive → provider → type catalogue, key sizes, usage rules |
| [cryptography/providers.md](cryptography/providers.md) | per-provider supported and unsupported algorithms |
| [infra/setup.md](infra/setup.md) | `:android` setup package |
| `modules/config/docs/config.md` | authored and generated config files, fields, precedence |
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
    - `src/main/kotlin/` : `Discovery` + `DiscoveryRun` at the package root — the entry point, the one file that sees every sub-package; everything else in sub-package folders
      - `adapter/` : reads the JCA and parses it into the contract — `ProviderProbe`, `PropertyMapIndex`, `PropertyKeyParser`, `PropertyKey`, `DeclaredAlias`, `AttributeKind`, `AttributeValueParser`, `DeviceRuntimeReader`
      - `contract/` : the captured model — `CapturedEnvironment`, `ProviderEntry`, `ServiceEntry`, `AliasEntry`, `ServiceAttributes`, `RuntimeInfo`, `ServiceKey`; the trial model — `TrialReport`, `ServiceTrialEntry`, `TransformationTrialEntry`, `TrialOutcome`
      - `setting/` : `DiscoverySettingConverter` → `DiscoverySetting`, the capture reduced to `BenchmarkScope`; `ProviderSetting`, `ServiceSetting`, `Device`, `ServiceLookup`
      - `query/` : questions asked of a capture or a trial, pure and data-returning — `CaptureQuery` (`whoServes`, `namesOf`, `onlyOn`, `tree`), `TrialQuery` (`failingServices`, `failingTransformations`, `instantiationByProvider`), `ServiceShape`, `TransformationFailure`, `ServiceIndex`, `ServiceTree`
      - `trial/` : `TrialRunner` — level 1, instantiates every captured service and declared cipher transformation → `TrialReport`; `DefaultRunTrial` — level 2, calls every instantiated one once with a default key (1024 bytes, then 32) → `defaultRun`; `Attempt`, `TransformationSet`
        - `call/` : one `DefaultCall` per engine type (`CipherCall`, `SignatureCall`, `MacCall`, `DigestCall`, `GeneratorCall`, `AgreementCall`), registry `DefaultCalls`, `DefaultKeys`, `KeyNames`, `KeyBits`
      - `write/` : `CaptureDocument` (schema, `of` ⇄ `parse`) → `EnvironmentYamlWriter` → `probe_<utc>.yaml`; `ProviderClassNameWriter` → `probe_classes_<utc>.yaml`; `TrialDocument` (`of` ⇄ `parse`) → `TrialYamlWriter` → `trial_<utc>.yaml`; `DocumentFields`, `YamlCodec`, `ProbeDirectory`, `ProbeFileName`
  - `modules/config/` : module `:config` (kotlin, java library) — environment's files × authored `config/` → `effective.yaml`; no module dependency
    - `README.md`, `docs/config.md` : module docs, field tables, precedence
    - `src/main/kotlin/`
      - `Configuration.kt` : entry point — `inventory(capture, trial)`, `effective(global)`
      - `source/` : environment's probe and trial files read as `DocumentReader`s
      - `inventory/` + `dto/` : what the device has — generated, overwritten every probe
      - `global/` + `dto/` : `global.yaml` — `selection`, `run`, `policy`; one section per feature
      - `testset/` + `dto/` : include / exclude / overrides rules
      - `effective/` + `dto/` : `EffectiveBuilder` (include → exclude → overrides → policy), `OverrideResolver`
      - `yaml/` : shared plumbing — `DocumentHandler` per file kind, `YamlFile` (schema stamp and check), `YamlFiles` factory
  - `modules/preparation/` : module `:preparation` (kotlin + legacy java, java library) — `effective.yaml` → cases with keys and bound parameters; never inside a measurement, runs on any JVM
    - `src/main/kotlin/`
      - `Preparation.kt` : entry point — `prepare(effective.yaml)` → `PreparedRun`; applies `policy.onFailure` to rejections, unplannable and ungeneratable keys; writes `results/preparation/skipped.yaml`
      - `prepare/` : `PreparedCase` (case, key recipe, key material — one per recipe, bound parameters), `PreparedRun`, `StoppedOnFailureException`
      - `report/` : `Skip` (the record every stage writes), `SkipFile`
      - `yaml/` : `YamlCodec` (duplicated)
      - `source/` : `ConfigSource` — `effective.yaml` read by key → `BenchmarkRequest`, one `Selection` per entry pinned to its provider; `ConfigFields` (no `:config` dependency); reads `policy.onFailure` into the request
      - `request/` : `BenchmarkRequest`, `Selection` (per-entry `inputSizes` override) — what the user wants measured, shape-validated
      - `measurement/` : `EngineTypeName` (case fold shared by the registries); `BenchmarkCase` — one measurement: type, algorithm as passed to `getInstance`, provider, key size, input size, `Phase` (WARM: instance built before the timer, Jetpack measures the loop; COLD: first call in a fresh process, timed once per process), `Metric` set (`CPU_EVENTS` needs a rooted device), seed; `CaseName` gives the `id` that links it to its result
      - `port/` : `DeviceCapability`, `Availability` — what preparation needs to know about the device
      - `adapter/` : `DiscoveryCapability` — the port answered from a capture and its trial; the only file importing `:environment:discovery`
      - `parameter/bind/` : `ParameterBinder` — `{class, arguments}` trees from `effective.yaml` → `AlgorithmParameterSpec` by reflection; `field`, nesting, `fresh(n)`, value conversion (`ValueCoercion`), `BindPolicy` (parameter-spec types only), `BoundParameters` (`next()`, `varies`), `BindException` (names the path)
      - `resolve/` : `CaseResolver(capability, rules, binder)` — `ParameterCheck` rejects a selection whose trees don't bind; → `Resolution(cases, rejections)`; `AxisRules` (engine type → `AxisRule`, fallback for unregistered types), `SelectionExpander`, `Rejection`
      - `key/plan/` : `KeyPlanner(capability, shapes)` — case → `KeyRecipe` (None, Secret, Pair, Unavailable), pure; `KeyShapes` (engine type → `KeyShape`, Cipher and unknown types decided by the device's generators), `KeyAlgorithmName`
      - `key/generate/` : `KeyMaterialGenerator(random, initializers, binder)` — recipe → `KeyMaterial`, the only key code calling the JCA; a bound `key:` spec wins over the size; `KeyInitializer` per provider, `DefaultKeyInitializer`
    - `src/main/java/.../preparation/workload/` : `DataType`, `StringType` — legacy input generation, used by the old tests
  - `modules/benchmark/` : module `:benchmark` *(planned, #33)* — the Jetpack harness: runs cases, times them, writes `benchmarkData.json`
  - `modules/android/` : module `:android` (application) — depends on all modules
    - `setup/config/` : `Config` — run parameters read from the pushed config
    - `src/androidTest/` : on-device benchmarks and functional tests
    - `src/test/` : JVM tests
    - `src/main/res/raw/` : `device_primitives.json` (old capture), `restrictions.json` (policy) — kept as data
  - `gradle.properties` : gradle env + signing + benchmark defaults
- `config/` : authored, committed — `global.yaml`, `testsets/{scope,all,smoke}.yaml`
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
  - `discovery/` : `probe_<utc>.yaml`, `probe_classes_<utc>.yaml`, `trial_<utc>.yaml` — same stamp, same capture
  - `configuration/` : `inventory.yaml` (generated), `effective.yaml` (what runs)
  - `preparation/` : `skipped.yaml`
  - `benchmark/`, `analysis/` : *(planned)*
- `CryptoBenchmark.config` : generated per run, pushed to the device
- `scripts/requirements.txt` : host python deps
- `docs/notas.md` : research notes

### language

| Module | Language | Inside a measurement |
|---|---|---|
| `:crypto` | Java | yes — it is the subject |
| `:preparation` | Kotlin, Java (legacy `workload/`) | no — prepares before the timed block |
| `:benchmark` *(planned)* | as `:crypto` | yes — it is the timed run |
| `:android` | Java | hosts the measurement classes in `androidTest` |
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

1. `discovery/` : determine device, runtime, hardware capability, benchmark compatibility
2. `setup/` : user config and user-supplied inputs (device state is Jetpack's, via runner args)
3. `preparation/` : algorithm, inputs, keys, parameters for one case
4. `benchmark/` : the timed run *(planned)*

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

Inside `:android`:

- `setup` : imports `discovery`
- `androidTest` : imports `preparation`, `crypto` (moves to `:benchmark` with #33)
