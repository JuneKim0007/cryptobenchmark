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
      - `codec/` : byte↔String, base64, charset *(planned — split out of `misc/Utils`)*
    - `setup/` : device facts; cannot affect a measurement
      - `DeviceCryptoPrimitives` : walks `Security.getProviders()`
      - `DevicePrimitiveRestrictions` : applies `res/raw/restrictions.json`
      - `CryptoProvider`, `CryptoPrimitive`, `ConfigurableCryptoPrimitive`, `CryptoParam`, `MultiCryptoParam` : provider/algorithm model
      - `config/` : reads the pushed run config *(planned)*
    - `bench/` : what to measure *(planned)*
      - `case/` : one measurement described — op, algorithm, mode, padding, provider, key size, input size
      - `registry/` : which cases exist = scope ∩ capability
      - `fixture/` : turns a case into a runnable thing — key, workload, spec
        - `workload/` : `DataType`, `StringType` — input generation
    - `misc/` : `Utils` — being split into `crypto/codec` and `setup/config`
  - `app/src/androidTest/` : on-device benchmarks and functional tests
  - `app/src/test/` : JVM tests
  - `app/src/main/res/raw/` : `device_primitives.json`, `restrictions.json`
  - `gradle.properties` : gradle env + signing + benchmark defaults
- `scripts/` : host side
  - `run_benchmarks.sh` : the sweep; entry point
  - `benchmark.py` : one run — build, install, push config, instrument, collect
  - `analyze_results.py` : validate results against logcat
- `docs/`
  - `cryptography/primitives.md` : primitives, providers, use
  - `cryptography/providers.md` : per-provider support and scope
  - `infra/setup.md` : setup classes
- `CryptoBenchmark.config` : generated per run, pushed to the device
- `requirements.txt` : host python deps
- `notas.md` : research notes

### dependency rules

- `crypto/primitive` : imports nothing from `setup` or `bench`
- `setup` : imports nothing from `crypto` or `bench`
- `bench/case` : imports nothing
- `bench/registry` : imports `case`, `setup`
- `bench/fixture` : imports `case`, `crypto/primitive`
- `androidTest` : imports `bench`, `crypto/primitive`
