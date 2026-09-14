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
    - `environment/` : everything around a measurement, never inside one
      - `discovery/` : what this device offers and whether it fits the benchmark
        - `DeviceCryptoPrimitives` : walks `Security.getProviders()`
        - `DevicePrimitiveRestrictions` : applies `res/raw/restrictions.json`
        - `CryptoProvider`, `CryptoPrimitive`, `ConfigurableCryptoPrimitive`, `CryptoParam`, `MultiCryptoParam` : provider/algorithm model
      - `setup/` : put the device into the required state — CPU affinity, governor, background processes, permissions, profiling tools, directories *(planned; mostly host-side today)*
      - `preparation/` : benchmark state built before measuring
        - `config/` : run parameters read from the pushed config
        - `case/` : one measurement described — op, algorithm, mode, padding, provider, key size, input size *(planned)*
        - `registry/` : which cases exist = scope ∩ discovery *(planned)*
        - `key/` : key per case *(planned)*
        - `workload/` : `DataType`, `StringType` — input generation
    - `misc/` : `Utils` — `getMethod` plus debug helpers; removed with the reflection dispatch
  - `app/src/androidTest/` : on-device benchmarks and functional tests
  - `app/src/test/` : JVM tests
  - `app/src/main/res/raw/` : `device_primitives.json`, `restrictions.json`
  - `gradle.properties` : gradle env + signing + benchmark defaults
- `scripts/` : host side
  - `run_benchmarks.sh` : the sweep; entry point
  - `benchmark.py` : one run — build, install, push config, instrument, collect
  - `analyze_results.py` : validate results against logcat
- `docs/`
  - `docs.md` : this file
  - `cryptography/primitives.md` : primitives, providers, use
  - `cryptography/providers.md` : per-provider support and scope
  - `infra/setup.md` : setup classes
- `CryptoBenchmark.config` : generated per run, pushed to the device
- `requirements.txt` : host python deps
- `notas.md` : research notes

### phases

1. `environment/discovery/` : determine device, runtime, hardware capability, benchmark compatibility
2. `environment/setup/` : configure the device into the required state
3. `environment/preparation/` : algorithm, inputs, keys, parameters for one case

### dependency rules

- `crypto/` : imports nothing from `environment`
- `environment/discovery` : imports nothing from `crypto` or the rest of `environment`
- `environment/setup` : imports `discovery`
- `environment/preparation` : imports `discovery`, `crypto`
- `androidTest` : imports `environment`, `crypto`

### rename pending

- `setup/` → `environment/discovery/`
- `setup/config/` → `environment/preparation/config/`
- `bench/fixture/workload/` → `environment/preparation/workload/`
