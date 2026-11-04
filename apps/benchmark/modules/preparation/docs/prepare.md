# prepare

`effective.yaml` to prepared cases, each called once. Operations, keys and parameter trees: [operations.md](operations.md). Outputs: [prepared.md](prepared.md). File map: [index.md](index.md).

## Flow

```
effective.yaml -> InboundFile -> GlobalReader -> PrimitiveReader -> BenchmarkRequest
probe_<utc>.yaml, trial_<utc>.yaml -> CaptureFile, TrialFile -> DiscoveryCapability
BenchmarkRequest + DiscoveryCapability -> CaseResolver -> cases + rejections
per case: KeyPlanner -> KeyMaterialGenerator -> bind parameters -> definition.input -> PreparedCase -> invocation.once()
-> PreparedRun -> skipped.yaml, prepared.yaml
```

| rule | value |
|---|---|
| callers | `DevicePlan` on the device (`apps/benchmark/modules/android`), `Bench.kt` in `apps/benchmark/cli` on the host |
| inputs | YAML only: effective.yaml, capture, trial |
| key cache | generated key material is cached per recipe across cases |
| registry | `EngineTypes.standard()`, read from `engine/engine-operations.yaml`, unless the caller passes another |

## Inputs

| file | schema | read |
|---|---|---|
| effective.yaml | `config` v1 | sections `run`, `policy`, `providers`, all required |
| capture | `capture` v1 | `capturedAtMillis`, `providers[].name`, `precedence`, `services[].type`, `algorithm`, `aliases` |
| trial | `trial` v2 | `services[].provider`, `type`, `algorithm`, `instantiates`, `error`, `transformations[]`; `keyAlgorithm` from `defaultRun.keyAlgorithm` |

| error | text |
|---|---|
| wrong schemaVersion | `unsupported_<schema>_schema: <file>: <n>, this build reads <m>` |
| missing file | `missing_file: <path>` |
| bad YAML, duplicate keys | `unreadable_yaml` |
| non-mapping | `not_a_mapping` |
| field | `missing_field: <key>`, `wrong_type: <key>`, `unknown_<field>: <name>, one of [...]` (enum match case-insensitive) |

## run and policy

| key | rule |
|---|---|
| `inputSizes` | required; non-empty, positive, distinct |
| `phases` | required; non-empty; `WARM`, `COLD` |
| `metrics` | required; `TIME`, `ALLOCATION`, `CPU_EVENTS`; must hold `TIME`, no repeats (`Metric.read` in `:settings`) |
| `variants` | optional, default `[fixed, notFixed]`; distinct values of `fixed`, `notFixed` ([operations.md](operations.md#variants)) |
| `processRepetitions` | required; `>= 1` |
| `seed` | required |
| `harness` | optional; settings key table |
| `policy.onFailure` | required; `STOP`, `SKIP` |

## Selections

`providers.<provider>.<type>.<name>[@<group>]: {entry}`; entry fields `keySizes`, `inputSizes`, `key`, `parameters`, `operations`, `harness`, all optional.

| rule | value |
|---|---|
| entry key | algorithm before `@`, group after `@` or empty |
| `inputSizes` empty | `run.inputSizes` |
| none selected | `nothing_selected: <file>` |
| validation | type and algorithm non-blank; group without `@`; `keySizes`, `inputSizes` positive and distinct |
| duplicates | `duplicate: selections` |

## Engine types

| type | operations |
|---|---|
| Cipher | ENCRYPT, DECRYPT |
| Signature | SIGN, VERIFY |
| Mac | COMPUTE_MAC |
| MessageDigest | DIGEST |
| KeyGenerator | GENERATE_KEY |
| KeyPairGenerator | GENERATE_KEY_PAIR |
| KeyAgreement | AGREE_KEY |
| any other | TYPE_DEFAULT |

Type names match case-insensitively. `with(type, operations)` returns a new registry.

## Resolution

| rule | value |
|---|---|
| operations | entry `operations` narrows the type's list |
| expansion | provider x operation x keySize x inputSize x phase x variant; variant innermost, so an item's two variants are adjacent |
| variant axis | `run.variants` for a type whose catalog row has two; one `fixed` case for a `variants: one` row (key generation) and a type the catalog lacks |
| keySize axis | only when the operation consumes key size and `keySizes` is set, else one null |
| inputSize axis | only when the operation consumes input, else one null |
| harness | `run.harness` merged with the entry's |
| metrics, seed | global values on every case |

| rejection | cause |
|---|---|
| `unsupported_operation: [..] for <type>, one of [..]` | entry operation not in the type |
| `key_parameters_and_key_sizes: set one; a key spec already fixes the size` | `key` and `keySizes` both set |
| `unused_setting: [..] reaches no call of [..]` | `keySizes`, `key` or `parameters` that no operation consumes |
| `bind_failed: <path>: <detail>` | `key` or `parameters` tree fails to bind |
| Availability reason | provider cannot serve the name |
| `no_provider` | no provider list and none available |

## Device availability

| rule | value |
|---|---|
| pairing | capture and trial share `capturedAtMillis`, else `mismatched_trial: capture <a>, trial <b>` |
| provider order | ascending `precedence` |
| lookup | registered algorithm or alias, case-insensitive |
| name with `/` | when not registered, checked as a transformation of the base Cipher service in the trial |
| reasons | `provider_not_installed`, `not_registered`, `not_tried`, `instantiation_fails: <error>`, `transformation_fails: <error>` |
| `measuredKeyAlgorithm` | the trial's `keyAlgorithm` for the service or transformation |

## Failures

| reason, prefixed `<caseId>: ` | stage |
|---|---|
| `KeyRecipe.Unavailable` reason | key plan |
| `key_generation_failed: <msg>` | key |
| `input_preparation_failed: <Exception>: <msg>` | input |
| `dry_run_failed: <Exception>: <msg>` | `once()` |

Resolve rejections become skips with stage `preparation`. Outcome under `policy.onFailure`: [prepared.md](prepared.md#onfailure).
