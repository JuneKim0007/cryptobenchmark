# config

Authored settings: `config/global*.yaml` and `config/testsets/*.yaml`, committed and written only by the user. Generated files: [generated.md](generated.md). File map: [index.md](index.md).

## Authored files

| file | selection.testSet | run | notes |
|---|---|---|---|
| `config/global.yaml` | `testsets/scope.yaml` | inputSizes `[64, 1024, 16384]`, seed 0 | harness `iterations: 100`; every other key takes its default |
| `config/global.reference.yaml` | `testsets/scope.yaml` | every key with its default and whether it is required | read by no stage; `CommittedConfigTest` parses it |
| `config/global-quick.yaml` | `testsets/quick.yaml` | inputSizes `[64, 1024, 16384]`, seed 42 | harness `{iterations: 5, profiling: none}`; analysis charts `[iqrBars, stability]` |
| `config/global-demo.yaml` | `testsets/smoke.yaml` | inputSizes `[1024]`, seed 42 | no harness |

| test set | contents |
|---|---|
| `testsets/all.yaml` | description only; empty include = whole inventory |
| `testsets/scope.yaml` | 19 includes, baselines MD5, DESede/CBC/PKCS5Padding, ARCFOUR; AES 128/192/256, `AES_<n>/*` variants their own size; a `fresh(n)` IV or nonce for every AES GCM, CBC and CTR name and variant, DESede/CBC, ChaCha20 and ChaCha20-Poly1305; RSA 2048/4096 with inputSizes `[32]`; OAEP-SHA256 with explicit `OAEPParameterSpec` |
| `testsets/quick.yaml` | 11 includes, one per primitive; AES 128/256 with the same variant and `fresh(n)` IV rules as scope; RSA/* keySizes `[2048]`, inputSizes `[32]`; harness iterations 5; ChaCha20 `ChaCha20ParameterSpec [fresh(12), 1]` |
| `testsets/smoke.yaml` | SHA-256; AES/GCM/NoPadding with keySizes `[256]`, GCM 128 + `fresh(12)`; HmacSHA256 |

Device time of a full Pixel run (inputSizes `[64, 1024]`, both variants, the three passes, `processRepetitions: 2`, `isolation: case`), estimates from the per-pass figures in [device-session.md](../../../docs/device-session.md#passes) (Pixel 10, about 0.11 s a sample):

| part | per case | why |
|---|---|---|
| one process of the three passes | timing 38 s + energy 20 s + allocation 15 to 30 s + 3 process starts of 1 to 2 s + temperature and clocks about 1 s = 80 to 95 s | samples set the time, so a `notFixed` case costs the same |
| `processRepetitions: 2` | 160 to 190 s | `energyJ` is one value per process; perf-repair's median interval and pImprove need two runs, so energy needs two processes; timing and allocation pay it too |
| cases | about 285, from 190 at `[64, 1024, 16384]` and one variant | the host plan of `scope.yaml` goes from 164 to 246 cases (x 1.5): two sizes instead of three (x 2/3 of the sized cases), two variants (x 2) of every item but key generation; the Pixel's is assumed the same shape |
| benchmark, about 285 cases | 12.5 to 15 h, plus heat pauses (31% of the last full session) | runs once per device, then only for used-set items it lacks |
| before/after, per scope | 2 sides x 3 repetitions x 80 to 95 s = 8 to 9.5 min | not split by variant: it times the app's function as written; ABBA over `scopedRepetitions: 3`; energy n = 3 per side |
| 50 apps, one scope each | 7 to 8 h, plus heat pauses | two scopes an app doubles it |
| thermal gate | unknown until measured: 0 s a case on a device that cools within its gap, at most 120 s a case | worst case `timeoutSeconds x cases` per pass: 285 cases x 120 s = 9.5 h a pass, three passes and two processes 57 h; a before/after scope at most 2 x 3 x 3 x 120 s = 36 min; the first overnight run's `gate:` lines give the real figure |

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
| | `variants` | `[fixed, notFixed]` | non-empty, distinct values of `fixed`, `notFixed`, else `invalid: run.variants`; preparation makes one case per variant of each item ([operations.md](../../preparation/docs/operations.md#variants)); `--harness` before/after runs ignore it |
| | `processRepetitions` | `1` | `>= 1`; independent process runs |
| | `isolation` | `case` | `case` or `run`, else `invalid: run.isolation`; `--device` only: `case` runs each measured case in its own instrumentation process, `run` all of them in one ([run.md](../../../docs/run.md#device-run)) |
| | `seed` | `0` | input seed |
| | `passes` | `{}` | map of `timing`, `energy`, `allocation` to `{samples: n}`, `n >= 1`, in run order; `timing` required when set (`missing_pass`); `allocation` needs `ALLOCATION` in `metrics` (`pass_without_metric`); another name `invalid`; [device-session.md](../../../docs/device-session.md#passes) |
| | `thermalThrottleSleepSeconds` | unset | `>= 0`, else `negative`; `--device`: passed as `-e androidx.benchmark.thermalThrottle.sleepDurationSeconds`; unset keeps Jetpack's default |
| | `warmup` | `{iterations: 10, jobs: []}` | `iterations >= 0`, else `negative`, 0 off; `jobs` test-set rules, `[]` the plan's first 3 cases; `--device` only ([device-session.md](../../../docs/device-session.md#warm-up)) |
| | `caseCooldownSeconds` | `0` | `>= 0`, else `negative`; `--device`: host sleep before every measured case but a session's first, between processes with `isolation: run` ([device-session.md](../../../docs/device-session.md#cool-down-and-frequency-caps)) |
| | `thermalGate` | absent: off | `{enabled?: true, sensors, marginCelsius?: 3, pollSeconds?: 5, timeoutSeconds?: 300}`; `sensors` non-empty when enabled (`missing_field`), the device's thermal HAL names; margin `>= 0`, timeout `>= 0` (`negative`), poll `>= 1` (`not_positive`); `enabled: false` off; written to `effective.yaml` only when set; `--device` only ([device-session.md](../../../docs/device-session.md#thermal-gate)) |
| | `scopedRepetitions` | `3` | `>= 1`, else `not_positive`; `--harness` only: processes per side, before and after in alternating order ([scoped.md](../../android/docs/scoped.md#order)) |
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
| sized variant | a wildcard matches `AES_128/...` by its canonical name `AES/...` too, so a variant's own `AES_128/*` rule goes after `AES/*`; an exact name never matches a variant |
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
