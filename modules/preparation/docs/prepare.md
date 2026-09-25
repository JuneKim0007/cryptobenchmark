# prepare

`effective.yaml` → prepared cases, and `prepared.yaml` describing them. Nothing here runs inside a measurement.

## Flow

```
effective.yaml ─► InboundFile ─► GlobalReader ─► PrimitiveReader ─► BenchmarkRequest
                                                                        │
probe_<utc>.yaml, trial_<utc>.yaml ─► CaptureFile, TrialFile ─► DiscoveryCapability ─► CaseResolver ─► cases + rejections
                                                                        │
                   KeyPlanner ─► KeyMaterialGenerator ─► OperationDefinition: input, then the invocation ─► PreparedRun
                                                                        │
                                                            PreparedFile ─► prepared.yaml
```

Each stage takes the previous stage's value, so the order is checked by the compiler.
Every inbound is a YAML file; no other module is on the classpath. Run settings come only from
`effective.yaml`: config owns their defaults, and preparation requires every field.

## Axes of one case

| Axis | From | Absent means |
|---|---|---|
| operation | `EngineTypes` per engine type; `operations` in the entry narrows it | every operation of the type |
| group | the entry key `<name>@<group>`; the device is asked about `<name>` alone | the primitive is measured once |
| key, key size, input | what the operation consumes (`operation/`), not what the type declares | the axis does not exist for that operation |
| key size | entry `keySizes`; a size written into the name (`AES_128`) | the provider's default |
| input size | entry `inputSizes`, else `run.inputSizes` | the type takes no input |
| phase | `run.phases` | — |
| harness | `run.harness`, field by field under the entry's `harness` | the harness's own defaults |
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
| `input_preparation_failed`, `dry_run_failed` | input, invocation |

`policy.onFailure` decides: `skip` records each in `results/preparation/skipped.yaml`, `stop` writes the report and exits.

## prepared.yaml

The run as built, for reading and for the harness to check itself against. One file per run,
always overwritten.

| Key | Holds |
|---|---|
| `generatedFrom.effective` | the file this run was read from |
| `run` | `seed`, `processRepetitions`, `harness` — the run's defaults |
| `cases[].id` … `metrics` | the case, as the case id spells it |
| `cases[].harness` | global merged with the entry's: what the timer is told for this case |
| `cases[].key` | `kind` (`none`, `secret`, `pair`), the recipe, and the built key's `encodedBytes` or `pairs` |
| `cases[].keyParameters`, `parameters` | the spec trees that reached the generator and the call |
| `cases[].specPerIteration` | present when a `fresh(n)` spec is drawn before every iteration |
| `cases[].input` | `kind` (`none`, `message`, `ciphertext`, `signedMessage`) and its sizes |
| `cases[].fingerprint` | SHA-256 of the case block, first 8 hex: a harness that resolved something else can see it |

No key material and no input bytes: both are reproducible from `seed` and the recipe, and a
benchmark file on a device is not a place for keys.

## Limits

- one call per case proves it runs; it says nothing about timing
- `prepared.yaml` is a record of what was built, not an input: nothing reads it back to rebuild a case
- the harness gets the same `Invocation`, so what is proved is what is measured
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
| `HarnessReader`, `HarnessSettings` | `global` | what the timer is told, global merged with the entry's |
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
| `OperationDefinition`, `OperationDefinitions`, `KeyShape` | `operation` | what each operation consumes (key, key size, input), and the call it builds |
| `Invocation`, `Invocations` | `operation` | `setUp` and `perIteration` for one case: called once here, timed by the harness |
| `EncryptDefinition` … `TypeDefaultDefinition` | `operation` | one definition per operation |
| `CaseArguments` | `operation` | the message, secret key or key pair a prepared case carries |
| `PreparedCase`, `PreparedRun`, `StoppedOnFailureException` | `prepare` | the output |
| `Skip`, `SkipFile` | `report` | `skipped.yaml` |
| `PreparedFile`, `PreparedDocument`, `Fingerprint` | `record` | `prepared.yaml`, written from the cases that were built |
| `DocumentFields`, `YamlCodec` | `shared` | typed reads, YAML text |
