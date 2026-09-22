# prepare

`effective.yaml` → prepared cases. Nothing here runs inside a measurement.

## Flow

```
effective.yaml ─► InboundFile ─► GlobalReader ─► PrimitiveReader ─► BenchmarkRequest
                                                                        │
probe_<utc>.yaml, trial_<utc>.yaml ─► CaptureFile, TrialFile ─► DiscoveryCapability ─► CaseResolver ─► cases + rejections
                                                                        │
                   KeyPlanner ─► KeyMaterialGenerator ─► OperationDefinition: input, then one call ─► PreparedRun
```

Each stage takes the previous stage's value, so the order is checked by the compiler.
Every inbound is a YAML file; no other module is on the classpath. Run settings come only from
`effective.yaml`: config owns their defaults, and preparation requires every field.

## Axes of one case

| Axis | From | Absent means |
|---|---|---|
| operation | `EngineTypes` per engine type; `operations` in the entry narrows it | every operation of the type |
| key, key size, input | what the operation consumes (`operation/`), not what the type declares | the axis does not exist for that operation |
| key size | entry `keySizes`; a size written into the name (`AES_128`) | the provider's default |
| input size | entry `inputSizes`, else `run.inputSizes` | the type takes no input |
| phase | `run.phases` | — |
| parameters | entry `key` and `parameters` trees | the provider fills them in |

## What each operation takes

Every setting in an entry reaches a Java call, or the entry is rejected with `unused_setting`.

| Operation | `keySizes` | `key` | `parameters` | input |
|---|---|---|---|---|
| ENCRYPT, DECRYPT | the key's generator | the key's generator | `Cipher.init` | yes |
| SIGN, VERIFY | the key's generator | the key's generator | `Signature.setParameter` | yes |
| COMPUTE_MAC | the key's generator | the key's generator | `Mac.init(key, spec)` | yes |
| DIGEST | — | — | — | yes |
| GENERATE_KEY, GENERATE_KEY_PAIR | the measured `init` | the measured `init` | — | — |
| AGREE_KEY | the keys' generator | the keys' generator | `KeyAgreement.init(key, spec)` | — |

A generator that is itself the measurement is initialised exactly as the config says and with no
`SecureRandom` of ours, so the provider's own source is what gets measured.

## Parameter trees

`{class, arguments}` by fully qualified name; an argument is a literal, `fresh(n)`, `{field: Class.NAME}`, or another tree.
Only subtypes of `AlgorithmParameterSpec`, `PSource` and `BigInteger` may be named. A failure names its path.

## Failures

| Reason | Stage |
|---|---|
| `provider_not_installed`, `not_registered`, `transformation_fails`, `not_tried` | resolve |
| `bind_failed: <path>`, `key_parameters_and_key_sizes`, `unsupported_operation`, `unused_setting` | resolve |
| `no_key_generator`, `key_generation_failed` | key |
| `input_preparation_failed`, `dry_run_failed` | input, check |

`policy.onFailure` decides: `skip` records each in `results/preparation/skipped.yaml`, `stop` writes the report and exits.

## Limits

- one call per case proves it runs; it says nothing about timing
- keys are reused across cases with the same recipe
- `fresh(n)` specs must be drawn before the timer; `BoundParameters.varies` says when
- `KeyInitializer` has one implementation on the host; the per-provider slot is for AndroidKeyStore
  and StrongBox, which generate keys through their own spec types (#33)

## Tunables

Contract keys stay with their readers and JCA names with the code that uses them; only these are choices.

| Value | Where | Default |
|---|---|---|
| which operations an engine type has | `EngineTypes.standard()`, passed once to `Preparation` | 7 types + a fallback of `TYPE_DEFAULT`; add one with `with(type, operations)` |
| what an operation consumes and how it is called once | one definition per `Operation` in `operation/` | the ten operations |
| which classes a parameter tree may name | `BindPolicy.standard()` | `AlgorithmParameterSpec`, `PSource`, `BigInteger` |
| how a key is initialised per provider | `KeyMaterialGenerator(initializers)` | `DefaultKeyInitializer` for every provider |

## Classes

| Class | Package | Role |
|---|---|---|
| `Preparation` | root | entry point: `prepare(effectiveFile)` → `PreparedRun`, applies `policy.onFailure` |
| `InboundFile`, `InboundDocument` | `inbound` | `effective.yaml` → sections, `schemaVersion` checked |
| `GlobalReader`, `GlobalSettings`, `OnFailure` | `global` | the `run` and `policy` sections |
| `PrimitiveReader` | `primitive` | the `providers` section → selections, against the global settings |
| `BenchmarkRequest`, `Selection` | `request` | what was asked for |
| `CaptureFile`, `TrialFile`, `ServiceName` | `device` | discovery's two files → DTOs; names folded for lookup |
| `CapturedDevice`, `CapturedProvider`, `CapturedService`, `Trialled*` | `device/dto` | the device as preparation reads it |
| `DeviceCapability`, `Availability` | `port` | what the device can run, and why not |
| `DiscoveryCapability` | `adapter` | the port over the capture and trial: registered name, alias, or transformation |
| `CaseResolver`, `SelectionCheck`, `SelectionExpander` | `resolve` | selections → cases or rejections |
| `Resolution`, `Rejection` | `resolve` | the result |
| `BenchmarkCase`, `CaseName`, `Operation`, `Phase`, `Metric`, `EngineTypeName` | `measurement` | one case and its id |
| `ParameterBinder`, `ValueNode`, `ValueCoercion`, `BindPolicy`, `BoundParameters`, `BindException` | `parameter/bind` | parameter trees → `AlgorithmParameterSpec` |
| `KeyPlanner`, `KeyAlgorithmName`, `KeyCandidate`, `KeyRecipe` | `key/plan` | which key a case needs, from which generator |
| `KeyMaterialGenerator`, `KeyInitializer`, `DefaultKeyInitializer`, `KeyMaterial` | `key/generate` | the key itself, cached per recipe |
| `InputBytes`, `OperationInput`, `CipherKeys` | `input` | seeded bytes, the input a case carries, the key a cipher takes |
| `EngineTypes` | `engine` | which operations an engine type has, and one fallback |
| `CaseEngines` | `engine` | the `Cipher` and `Signature` for a case |
| `OperationDefinition`, `OperationDefinitions`, `KeyShape` | `operation` | what each operation consumes (key, key size, input) and the one call that proves it runs |
| `EncryptDefinition` … `TypeDefaultDefinition` | `operation` | one definition per operation |
| `CaseArguments` | `operation` | the message, secret key or key pair a prepared case carries |
| `PreparedCase`, `PreparedRun`, `StoppedOnFailureException` | `prepare` | the output |
| `Skip`, `SkipFile` | `report` | `skipped.yaml` |
| `DocumentFields`, `YamlCodec` | `shared` | typed reads, YAML text |
