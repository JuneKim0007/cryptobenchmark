# config

Authored settings: `config/global*.yaml` and `config/testsets/*.yaml`, committed and written only by the user. Generated files: [generated.md](generated.md). File map: [index.md](index.md).

## Authored files

| file | selection.testSet | run | notes |
|---|---|---|---|
| `config/global.yaml` | `testsets/scope.yaml` | inputSizes `[64, 1024, 16384]`, seed 0 | harness `iterations: 100`; every other key takes its default |
| `config/global.reference.yaml` | `testsets/scope.yaml` | every key with its default and whether it is required | read by no stage; `CommittedConfigTest` parses it |
| `config/global-quick.yaml` | `testsets/quick.yaml` | inputSizes `[64, 1024, 16384]`, seed 42 | harness `{iterations: 5, profiling: none}`; analysis charts `[iqrBars, stability]` |
| `config/global-demo.yaml` | `testsets/smoke.yaml` | inputSizes `[1024]`, seed 42 | no harness |
| `config/global-energy.yaml` | `testsets/energy-smoke.yaml` | inputSizes `[1024]`, seed 42 | harness `iterations: 20`, energy `{capture: measured, windowSeconds: 3, warmupSeconds: 1, cooldownSeconds: 1}` |

| test set | contents |
|---|---|
| `testsets/all.yaml` | description only; empty include = whole inventory |
| `testsets/scope.yaml` | 19 includes, baselines MD5, DESede/CBC/PKCS5Padding, ARCFOUR; AES 128/192/256; RSA 2048/4096 with inputSizes `[32]`; OAEP-SHA256 with explicit `OAEPParameterSpec`; ChaCha20 with `fresh(12)` |
| `testsets/quick.yaml` | 11 includes, one per primitive; RSA/* keySizes `[2048]`, inputSizes `[32]`; harness iterations 5; ChaCha20 `ChaCha20ParameterSpec [fresh(12), 1]` |
| `testsets/smoke.yaml` | SHA-256; AES/GCM/NoPadding with keySizes `[256]`, GCM 128 + `fresh(12)`; HmacSHA256 |
| `testsets/energy-smoke.yaml` | the smoke staples; AES-GCM override adds `harness.energy.capture: dry` |

Primitive and provider catalogue: `docs/cryptography/primitives.md`.

## global.yaml

`schemaVersion: 1`. Sections `selection` (required), `run`, `policy`, `analysis`, `providers`; any other top key fails `unknown_section`; an unknown key fails `unknown_keys`.

| section | key | default | rule |
|---|---|---|---|
| `selection` | `testSet` | required | non-blank; relative to global.yaml's directory unless absolute |
| | `exclude` | `[]` | rules dropped after the test set |
| `run` | `inputSizes` | `[1024]` | non-empty, all `> 0`; bytes per call |
| | `phases` | `[WARM]` | non-empty, non-blank; values `WARM`, `COLD` checked by preparation |
| | `metrics` | `[TIME]` | `TIME`, `ALLOCATION`, `CPU_EVENTS`; must hold `TIME`, no repeats (`Metric.read`); device support checked at effective build: `modules/settings/docs/settings.md#device-support`; `benchmark.json` reports only these; ALLOCATION not requested: androidx still runs its allocation phase on a device; it is not reported |
| | `processRepetitions` | `1` | `>= 1`; independent process runs |
| | `isolation` | `case` | `case` or `run`, else `invalid: run.isolation`; `--device` only: `case` runs each measured case in its own instrumentation process, `run` all of them in one ([run.md](../../../docs/run.md#device-run)) |
| | `seed` | `0` | input seed |
| | `harness` | empty | key table in `modules/settings/docs/settings.md`; energy keys in `docs/energy.md` |
| `policy` | `onFailure` | `skip` | `stop` or `skip`, case-insensitive; other: `invalid: policy.onFailure` |
| `analysis` | `charts` | `[iqrBars, throughput, latency, stability]` | names from that list, no duplicates; `[]` draws none; another name fails `invalid: analysis.charts` |
| | `dir` | unset: `<device folder>/chart/<run-id>` | non-blank; `<run-id>` in it is replaced by the run id |
| | `statistic.headline` | `auto` | `auto`, `median`, `mean`; the statistic that leads in the chart summary |
| | `statistic.meanUpToCovPercent` | `5` | `> 0`; `auto` leads with the mean at or below this CoV, else the median; also the stability limit |
| | `units.latency` | `ms` | `ms`, `us`, `ns`; display only, results stay ns/op; else `invalid: analysis.units.latency` |
| | `units.throughput` | `MB/s` | `MB/s` (10⁶ bytes), `MiB/s`, `ops/s`; MB/s and MiB/s only where a case has an input size; else `invalid: analysis.units.throughput` |
| `providers` | `bundled` | `[]` | list of `{artifact, create, alias?}`; no duplicate artifact or alias |
| | `bundled[].artifact` | required | `group:name:version`, no comma or whitespace; else `invalid_artifact` |
| | `bundled[].create` | required | `fully.qualified.Class` (public no-argument constructor) or `fully.qualified.Class#staticFactory`; else `invalid_create` |
| | `bundled[].alias` | unset | non-blank, no whitespace; the name the provider is registered under; required on the device when its own name is already installed |

`onFailure` governs selected primitives that cannot run. A broken authored file (parse, `schemaVersion`, unknown section or key) always stops.

`analysis` is read by `tools/quick-bench/analyze.py` and `charts.py`; `scripts/pipeline.py` records `analysis.units` in `manifest.yaml`, where perf-repair reads it (`docs/tools.md`, `docs/results.md`). It is left out of the run's input digest, so a change reruns no measurement and applies from the next run's manifest.

`providers.bundled` is for `--device` runs. `scripts/pipeline.py` passes each `artifact` to the app build as `-PbundledArtifacts=a:b:1,c:d:2`, so it becomes an `implementation` dependency of `modules/android`. It also passes the list to `DeviceProbe`. On the device, discovery's `BundledInstaller` creates each provider by reflection and appends it after every platform provider. The capture then records it with `origin: bundled` and its `artifact`. A name that is already installed needs `alias`; without one the install fails with `bundled_name_taken`. Fields: `modules/environment/discovery/docs/probe.md`.

## testsets/*.yaml

`schemaVersion: 1`. An unknown key fails `unknown_keys: testSet`.

| key | rule |
|---|---|
| `description` | free text |
| `include` | rules; empty = every primitive the inventory can run |
| `exclude` | rules |
| `overrides` | list of `{match: rule, set: {...}}` |

| `set` key | rule |
|---|---|
| `keySizes`, `inputSizes` | all `> 0` |
| `operations` | non-empty, non-blank |
| `key`, `parameters` | parameter trees, passed through untouched |
| `harness` | settings key table; merges field by field |
| any other | refused |
| none set | `empty_override` |

## Rules

`{provider?, type?, name?, group?}`.

| rule | value |
|---|---|
| required | at least one of `provider`, `type`, `name` |
| blank part | refused |
| `group` | needs `name`; may not contain `@` |
| `provider`, `type` | equal ignoring case; missing = any |
| `name` | same canonical name and key size (`perf-repair/src/perfrepair/catalog/algorithm-names.yaml`), so `SHA256` matches `SHA-256`; missing = any |
| `name` with `*` | case-insensitive pattern, `*` = any text, against the given or the canonical spelling |
| error path | e.g. `include[0]`, `overrides[2].match`, `selection.exclude[0]` |

## Override precedence

| specificity part | weight |
|---|---|
| `group` | 16 |
| `provider` | 8 |
| exact `name` | 4 |
| wildcard `name` | 2 |
| `type` | 1 |

| rule | value |
|---|---|
| order | ascending specificity, ties by file order; the last applicable override wins per key |
| lists | replace |
| `harness` | merges field by field, nested `energy` and `cpu` too |
| override without `group` | applies to every group of that name |
| override with `group` | applies to that group only |

## Groups

One primitive measured more than once under different settings. Each distinct `group` of the includes that match a primitive yields one entry `<name>@<group>`; an include with no group yields the plain name. The device is asked about the name only.

```yaml
include:
  - {type: KeyPairGenerator, name: EC, group: p256}
  - {type: KeyPairGenerator, name: EC, group: p384}
overrides:
  - match: {type: KeyPairGenerator, name: EC, group: p256}
    set: {key: {class: java.security.spec.ECGenParameterSpec, arguments: [secp256r1]}}
```

## Parameter trees (`key`, `parameters`)

Config passes trees through as maps. Preparation binds them: forms in `modules/preparation/docs/operations.md#parameter-trees`.
