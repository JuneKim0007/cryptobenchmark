# config

Authored settings: `config/benchmark/global.yaml` and `config/benchmark/testsets/*.yaml`, committed and written only by the user. `algorithms/vectors/` holds the end-to-end check's sourced vectors; the benchmark module reads it ([check.md](../../benchmark/docs/check.md)), config does not. Generated files: [generated.md](generated.md). File map: [index.md](index.md).

## Authored files

| file | selection.testSet | run | notes |
|---|---|---|---|
| `config/benchmark/global.yaml` | `testsets/default_predefined.yaml` | inputSizes `[64, 1024, 16384]`, seed 0, variants default | harness `iterations: 100`; `providers.bundled` Conscrypt 2.9.0 as `BundledConscrypt`, BouncyCastle 1.87 as `BundledBC`; every other key takes its default |

| test set | contents |
|---|---|
| `testsets/default_predefined.yaml` | paper tiers 1–4 on AndroidOpenSSL, BundledConscrypt, BundledBC and AndroidKeyStore: operations `variants: [fixed, notFixed]`, software key generation `[fixed]`, AndroidKeyStore `[secure]`; then breadth, BouncyCastle-only, legacy, post-quantum and AndroidKeyStore rows; one provider-less rule per JCA type adds every other inventory primitive at provider-chosen parameters; per-row overrides, `Cipher RSA/*` inputSizes `[32]`; no excludes |

The tests' own global and test-set files (`global-check.yaml` for CI's end-to-end check, `global-smoke.yaml`) are in `apps/benchmark-runner/tests/fixtures/config/`.

Primitive and provider catalogue: `docs/cryptography/primitives.md`.

## global.yaml

`selection.knownVectors` (optional): a folder of `<family>.yaml` known answers read by `--check` beside the packaged ones, relative to the global file; a missing folder stops the run. A user vector needs no catalogue link: it reaches every case it matches by type, algorithm or an alias, operation and key size, and one that matches no case of the run is an `orphan_vector` warning.

`schemaVersion: 1`. Sections `selection` and `run` (required: `run.orderSeed`), `policy`, `analysis`, `providers`; any other top key fails `unknown_section`; an unknown key fails `unknown_keys`.


A composition of layers: [layers.md](layers.md).

| section | key | default | rule |
|---|---|---|---|
| `selection` | `testSet` | required | non-blank; relative to global.yaml's directory unless absolute |
| | `exclude` | `[]` | rules dropped after the test set |
| `run` | `inputSizes` | `[1024]` | non-empty, all `> 0`, distinct (`duplicate: inputSizes`); bytes per call |
| | `phases` | `[WARM]` | non-empty, distinct; `WARM` (`Phase.read` in `:settings`: `unknown_phase: <p>, one of [WARM]`) |
| | `metrics` | `[TIME]` | `TIME`, `ALLOCATION`; must hold `TIME`, no repeats (`Metric.read`); `benchmark.json` reports only these, whatever androidx runs ([measure.md](../../benchmark/docs/measure.md#jetpack-conversion)) |
| | `variants` | `[fixed, notFixed, secure]` | the execution paths every entry inherits ([entry.md](entry.md#variants)) |
| | `processRepetitions` | `1` | `>= 1`; independent process runs |
| | `seed` | `0` | input seed |
| | `passes` | `{}` | map of `timing`, `energy`, `allocation` to `{samples: n}`, `n >= 1`, in run order; `energy` also `minWindowSeconds` (default `5`, always written, `>= 1` else `not_positive`; on another pass `not_supported`); `timing` required with two or more passes (`missing_pass`); a single pass is its own base; `allocation` needs `ALLOCATION` in `metrics` (`pass_without_metric`); another name `invalid`; any pass also `thermalGate` (merged key by key over the resolved `run.thermalGate`, or over the defaults without one, where it must name `temperatureKeptCelsius`: `missing_field: run.passes.<p>.thermalGate.temperatureKeptCelsius`; written in full, and only for a pass that writes it; `null` is absent) and `caseCooldownSeconds` (`>= 0`, written only when set; replaces `run.caseCooldownSeconds` for that pass); an overlay that writes `run.passes` replaces the whole block ([layers.md](layers.md)); a pass gate leaf it does not write is named in `generatedFrom.settings` as `<run leaf's source> via run.thermalGate`; [device-session.md](../../../../../docs/device-session.md#passes) |
| | `thermalThrottleSleepSeconds` | unset | `>= 0`, else `negative`; `--device`: passed as `-e androidx.benchmark.thermalThrottle.sleepDurationSeconds`; unset keeps Jetpack's default |
| | `warmup` | `{iterations: 10, jobs: [], cases: 3}` | `iterations >= 0`, else `negative`, 0 off; `jobs` test-set rules, resolved to the entries they select; `[]` the plan's first `cases` cases (`>= 1`, else `not_positive`); `--device` only ([device-session.md](../../../../../docs/device-session.md#warm-up)) |
| | `caseCooldownSeconds` | `0` | `>= 0`, else `negative`; `--device`: host sleep before every measured case but a session's first ([device-session.md](../../../../../docs/device-session.md#cool-down-and-frequency-caps)) |
| | `thermalGate` | absent: off | keys in `example/config_global_example.yaml`; `temperatureKeptCelsius` required (`missing_field`), every other key merged key by key over its default (`ThermalGate.DEFAULTS`, in defaults.yaml) and written in full; minutes, limits and retries whole numbers (`not_whole: <key> <value> at <path>`) |
| | `launchRetries` | `2` | extra launches of a run that failed for a reason other than heat or a final preparation skip ([device-session.md](../../../../../docs/device-session.md#thermal-gate)) |
| | `energyIdleSeconds` | `120` | `>= 1`, else `not_positive`; `--device` with energy: the length of the idle readings before the first pass and after the last, whose interpolated power every energy window subtracts; part of a run's identity ([energy.md](../../../../../docs/energy.md#pre-flight)) |
| | `resumeBlockRuns` | `10` | `>= 1`, else `not_positive`; host only: a rerun of a stopped run with the same identity keeps its finished blocks of this many consecutive runs ([results.md](../../../../../docs/results.md#resuming-a-stopped-run)) |
| | `orderSeed` | required: absent is `missing_field: run.orderSeed`, every run, a host's too | a whole number; `--device` and `--bench`: each process shuffles the items with `Random("<seed>:<repetition>")`, an item's variants kept adjacent ([device-session.md](../../../../../docs/device-session.md)); part of a run's identity ([results.md](../../../../../docs/results.md#resuming-a-stopped-run)) |
| | `harness` | empty | key table in `apps/benchmark/modules/settings/docs/settings.md`; energy keys in `docs/energy.md` |
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

```yaml
run:   # a pass's own gate and cool-down, key by key over the run's; every key: example/config_global_example.yaml
  thermalGate: {temperatureKeptCelsius: 36.0, cooldownMinutes: 3}
  passes:
    timing: {samples: 50}                                   # holds under run.thermalGate
    energy: {samples: 100, thermalGate: {startMargin: {initialCelsius: 0.5}}, caseCooldownSeconds: 5}   # 36.0 C, 3 min, margin 0.5
```

Defaults are `lib/cryptobench/cryptobench/shared/settings/defaults.yaml`, which `DefaultsDocument` writes and the Python readers read. A `--bench` run ignores `passes`, `thermalThrottleSleepSeconds`, `warmup`, `caseCooldownSeconds`, `thermalGate`, `launchRetries`, `energyIdleSeconds` and `harness.warmupIterations`, `profiling`, `cpu`: each set to other than its default is one `ignored_on_host: <key> is set` warning, or its own line for `passes` and `thermalGate` (the `host` column of `lib/cryptobench/cryptobench/shared/settings/effective_view.py` KEYS).

`onFailure` governs selected primitives that cannot run. A broken authored file (parse, `schemaVersion`, unknown section or key) always stops.

`analysis` is read by `apps/benchmark-runner/analysis/analyze.py` and `charts.py`; `apps/benchmark-runner/pipeline.py` records `analysis.units` in `manifest.yaml`, where perf-repair reads it (`docs/tools.md`, `docs/results.md`). It is left out of the run's input digest: a change reruns no measurement and applies from the next run's manifest.

`providers.bundled` is for `--device` runs. `apps/benchmark-runner/pipeline.py` passes each `artifact` to the app build as `-PbundledArtifacts=a:b:1,c:d:2`, an `implementation` dependency of `apps/benchmark/modules/android`. It also passes the list to `DeviceProbe`. On the device, discovery's `BundledInstaller` creates each provider by reflection and appends it after every platform provider. The capture then records it with `origin: bundled` and its `artifact`. A name that is already installed needs `alias`; without one the install fails with `bundled_name_taken`. Fields: `apps/benchmark/modules/environment/discovery/docs/probe.md`.

## testsets/*.yaml

`schemaVersion: 1`. An unknown key fails `unknown_keys: testSet`.

| key | rule |
|---|---|
| `description` | free text |
| `include` | rules, each with an optional `variants` ([entry.md](entry.md#variants)); empty = every primitive the inventory can run |
| `exclude` | rules |
| `overrides` | list of `{match: rule, set: {...}}` |

| `set` key | rule |
|---|---|
| `keySizes`, `inputSizes` | all `> 0`; on an entry whose operations use no key size or input, preparation skips it `unused_setting` |
| `operations` | non-empty, non-blank |
| `variants` | [entry.md](entry.md#variants) |
| `key` | a parameter tree, plus `algorithm` and `provider` ([entry.md](entry.md#key-source)); on an entry whose operations take no key spec, preparation skips it `unused_setting` |
| `parameters` | a parameter tree, passed through untouched; on an entry whose operations take no parameters, preparation skips it `unused_setting` |
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
| `name` | same canonical name and key size (`algorithms/algorithm-names.yaml`): `SHA256` matches `SHA-256`; missing = any |
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
| sized variant | a wildcard matches `AES_128/...` by its canonical name `AES/...` too; a variant's own `AES_128/*` rule goes after `AES/*`; an exact name never matches a variant |
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

Config passes trees through as maps, checking only a key's source. Preparation binds them: forms in `apps/benchmark/modules/preparation/docs/operations.md#parameter-trees`.
