# <docs>

## file structure

- `android/` : gradle project
  - `app/src/main/java/com/example/cryptobenchmark/`
    - `crypto/` : cryptography, nothing else
      - `primitive/` : one algorithm call per function, no iteration, no lookup
        - `cipher/` : `EncryptOperation`, `DecryptOperation` — the two call shapes
          - `symmetric/` : AES, DESEDE, ChaCha20, ARC4 — encrypt, decrypt, keygen
          - `asymmetric/` : RSA — encrypt, decrypt, keygen
        - `digest/` : SHA family, MD5
        - `mac/` : HMAC
        - `signature/` : sign, verify, signature keygen
      - `codec/` : byte↔String, base64, charset
    - `environment/` : the device and its state, never inside a measurement
      - `discovery/` : what this device offers — see `probe.md`, `security_contract.md`
        - `ProviderProbe` : reads the JCA into a capture
        - `CapturedEnvironment`, `ProviderEntry`, `ServiceEntry`, `ServiceAttributes`, `RuntimeInfo` : the capture model
        - `PropertyKey`, `ServiceKey`, `AttributeKind` : property-map classification and keys
        - `EnvironmentJsonWriter` : capture → JSON
        - `DiscoverySettingConverter` → `DiscoverySetting` : capture reduced to what the benchmark needs
      - `setup/` : what the user asked for — run config and user-supplied inputs
        - `config/` : `Config` — run parameters read from the pushed config
    - `benchmark/` : what is measured
      - `preparation/` : turns what the user asked for into runnable state
        - `case/` : one measurement described — op, algorithm, mode, padding, provider, key size, input size *(planned)*
        - `registry/` : case registry *(planned — provider lookup is `DiscoverySetting.providersFor` for now)*
        - `key/` : key per case *(planned)*
        - `workload/` : `DataType`, `StringType` — input generation
  - `app/src/androidTest/` : on-device benchmarks and functional tests
  - `app/src/test/` : JVM tests
  - `app/src/main/res/raw/` : `device_primitives.json` (old capture), `restrictions.json` (policy) — kept as data
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

### phases

1. `environment/discovery/` : determine device, runtime, hardware capability, benchmark compatibility
2. `environment/setup/` : user config and user-supplied inputs (device state is Jetpack's, via runner args)
3. `benchmark/preparation/` : algorithm, inputs, keys, parameters for one case

### dependency rules

- `crypto/` : imports nothing from `environment` or `benchmark`
- `environment/discovery` : imports nothing from `crypto` or `benchmark`
- `environment/setup` : imports `environment/discovery`
- `benchmark/preparation` : imports `environment/discovery`, `crypto`
- `androidTest` : imports `benchmark`, `crypto`
