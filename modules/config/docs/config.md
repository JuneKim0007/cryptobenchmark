# <config>

Two kinds of file, never mixed:

| | Files | Owner | Written by |
|---|---|---|---|
| authored | `config/global.yaml`, `config/testsets/*.yaml` | the user, committed | the user only |
| generated | `results/configuration/inventory.yaml`, `effective.yaml` | this module | every probe / every run |

## Flow

```
probe_<utc>.yaml + trial_<utc>.yaml ─► InventoryBuilder ─► inventory.yaml        what the device has (observations only)
global.yaml ─► selection.testSet ─► testsets/<name>.yaml ─┐
inventory.yaml ───────────────────────────────────────────┴─► EffectiveBuilder ─► effective.yaml   what will run (preparation reads only this)
```

EffectiveBuilder: include (empty = everything that runs) → test-set exclude → global exclude (exclude always wins)
→ overrides, broadest rule first → `policy.onUnavailable`.

## global.yaml

One section per feature, one owner each; an unknown section or key is an error.

| Section | Key | Default | Meaning |
|---|---|---|---|
| `selection` | `testSet` | required | path, relative to global.yaml |
| | `exclude` | `[]` | rules dropped after the test set |
| `run` | `inputSizes` | `[1024]` | bytes per call |
| | `phases` | `[WARM]` | `WARM`, `COLD` |
| | `metrics` | `[TIME]` | `TIME`, `ALLOCATION`, `CPU_EVENTS` (rooted device) |
| | `processRepetitions` | `1` | independent process runs |
| | `seed` | `0` | input seed |
| `policy` | `onFailure` | `skip` | every stage: a selected primitive that cannot run is `skip`ped and recorded, or the run `stop`s. A broken authored file (parse, `schemaVersion`, unknown section or key) always stops |

## testsets/*.yaml

| Key | Meaning |
|---|---|
| `description` | free text |
| `include` | rules; empty = every primitive the inventory can run |
| `exclude` | rules |
| `overrides` | `{match: rule, set: {keySizes?, inputSizes?, key?, parameters?, operations?}}` |

Rule: `{provider?, type?, name?}`; a missing part matches anything, case-insensitive, `*` is a wildcard.
Override precedence, lowest first: type → name pattern → exact name → provider. Ties: file order. Lists replace.

## effective.yaml

| Key | Meaning |
|---|---|
| `generatedFrom` | global, test set, inventory, capture, trial file names; device |
| `run` | the global `run` section, frozen |
| `policy` | the global `policy` section, frozen: preparation and the benchmark apply the same rule |
| `providers.<p>.<type>.<name>` | `keySizes`, `inputSizes`, `key`, `parameters`, `operations` (empty = every operation of the type), `providerDefaults` |
| `providerDefaults` | what is still the provider's choice: `keySize`, `parameters`, `modeAndPadding` |
| `warnings` | rules that touched nothing: `exclude_matches_nothing`, `override_matches_nothing` — usually a typo; not a failure, printed by the host command |
| `skipped` | `{stage, provider?, type?, name?, reason}`: `no_match` (include found nothing) or `not_runnable: <error>`; the same record preparation writes to `results/preparation/skipped.yaml` |

A size no override sets stays empty (provider default): an observed size is not a valid init argument
(DESede's default key encodes to 192 bits; `init` accepts 112 or 168). The observed size is in `inventory.yaml`.

## Errors and output files

| Situation | Result |
|---|---|
| a file is missing | `missing_file: <path>`; a test set also names the setting that pointed there |
| a file does not parse or has a wrong key | `<file>: <code>: <location>`, e.g. `scope.yaml: unknown_keys: include[0] [nme]` |
| a run fails | the previous `inventory.yaml` / `effective.yaml` is removed first, so no stale file survives |
| a file is written | written to `<name>.partial`, then moved into place |
| host command | expected errors print one `error:` line and exit 1; warnings and skips go to stderr |

## Parameter trees (`key`, `parameters`)

Passed through untouched; bound by preparation.

| Form | Means |
|---|---|
| `{class: <fully qualified name>, arguments: [...]}` | public constructor, tried in turn for the argument count |
| `{field: <fully qualified class>.<NAME>}` | public static field |
| `fresh(n)` | n new random bytes on every call |
| `!!binary <base64>` or `[0, 1, 255]` | `byte[]` |
| a number | `int`, `long` or `BigInteger`, whichever the constructor takes |

Only subtypes of `AlgorithmParameterSpec`, `PSource` and `BigInteger` may be named.

## Code

| Package | Holds |
|---|---|
| root | `Configuration` — `inventory(capture, trial)`, `effective(global)` |
| `source/` | environment's probe and trial files read as `DocumentReader`s |
| `inventory/`, `inventory/dto/` | `InventoryBuilder`, `InventoryDocument`; `Inventory`, `InventoryEntry`, `InventorySource` |
| `global/`, `global/dto/` | `GlobalDocument` (section list), `RunDocument`, `PolicyDocument`; `GlobalConfig`, `Selection`, `RunSettings`, `Policy` |
| `testset/`, `testset/dto/` | `TestSetDocument`, `RuleDocument`; `TestSet`, `Rule`, `Override` |
| `effective/`, `effective/dto/` | `EffectiveBuilder`, `OverrideResolver`, `EffectiveDocument`, `StoppedOnFailureException`; `EffectiveConfig`, `EffectiveEntry`, `EffectiveSource`, `Skip` |
| `yaml/` | shared plumbing: `DocumentReader` / `DocumentHandler` (per kind: value ⇄ map), `ReadOnlyYamlFile` (load, `schemaVersion` check) and `YamlFile` (+ stamp, overwrite), `YamlFiles` (factory: `at` for read-write, `readOnly` for environment's files), `ProviderTree`, `DocumentFields`, `YamlCodec` |

## Provider-specific, observed on JDK 25

| Observation | Handling |
|---|---|
| spelling chosen by provider (`AES/CBC/PKCS5PADDING`) | rules and names compared ignoring case |
| size inside the name (`AES_128/GCM/NoPadding`) | fixed by the name |
| default key sizes differ between providers (RSA 3072 JDK / 2048 Conscrypt) | recorded in the inventory; set explicitly in the test set to compare |
| input limits (RSA, `NONEwithDSA` 20 bytes) | `inputSizes` observed in the inventory, carried unless overridden |
| needs parameters not given by default (PBE, RSASSA-PSS, `SunTls*`) | `runs: false` with the reason; include them with `parameters` |
| no two JVM providers serve the same name | cross-provider behaviour unverified until a device run (#14) |
| SunJCE `ChaCha20` encrypts with a random nonce it does not expose in `getParameters()` | decrypt needs an explicit `ChaCha20ParameterSpec` with `fresh(12)`; set in `scope.yaml` |
