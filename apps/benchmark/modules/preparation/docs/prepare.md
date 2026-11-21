# prepare

`effective.yaml` to prepared cases, each called once. Operations, keys and parameter trees: [operations.md](operations.md). Outputs: [prepared.md](prepared.md). File map: [index.md](index.md).

## Flow

```
effective.yaml -> InboundFile -> GlobalReader -> PrimitiveReader -> BenchmarkRequest
probe_<utc>.yaml, trial_<utc>.yaml -> CaptureFile, TrialFile -> DiscoveryCapability
BenchmarkRequest + DiscoveryCapability -> CaseResolver -> cases + rejections
-> Listing (Preparation.list: no key made, no provider called)
one named case (Preparation.prepareOne): KeyPlanner -> KeyMaterialGenerator -> bind parameters -> definition.input -> PreparedCase -> invocation.once()
```

| rule | value |
|---|---|
| callers | `RunnablePlan` (`apps/benchmark/modules/benchmark`), used by `DevicePlan` on the device and `BenchKt`, `CheckKt` on the host; it writes `skipped.yaml` and `prepared.yaml`, preparation writes no file |
| failure | a failed step throws `PreparationException` (`key_generation_failed`, `input_preparation_failed`, `dry_run_failed`, `parameters_unreadable`, or the key recipe's reason); an Exception or LinkageError is wrapped with the step's code, any other Error escapes unwrapped |
| inputs | YAML only: effective.yaml, capture, trial |
| key cache | generated key material is cached per recipe across cases |
| registry | `EngineTypes.standard()`, read from `algorithms/engine-operations.yaml` (the build puts it beside the class), unless the caller passes another |

## Inputs

| file | schema | read |
|---|---|---|
| effective.yaml | `config` v2 | sections `run`, `policy`, `providers`, all required |
| capture | `capture` v1 | `capturedAtMillis`, `providers[].name`, `precedence`, `services[].type`, `algorithm`, `aliases` |
| trial | `trial` v3 | `services[].provider`, `type`, `algorithm`, `instantiates`, `error`, `transformations[]`; `keyAlgorithm` and `fixedKeySize` from `defaultRun` |

| error | text |
|---|---|
| wrong schemaVersion | `unsupported_schema_version: <file>: <n>, this build reads <m>` |
| missing file | `missing_file: <path>` |
| bad YAML, duplicate keys | `unreadable_yaml` |
| non-mapping | `not_a_mapping` |
| field | `missing_field`, `wrong_type`, `unknown_<field>: <name>, one of [...]` (enum match case-insensitive); `<code>: <file>: <key>` while the file is read, `<code>: <key>` for run, policy and selections checked after it |
| unknown key | `unknown_keys: <file>: effective [..], known [..]` at the top level, `unknown_keys: run [..], known [..]` after it, as config refuses it |

## run and policy

Config refuses a run that breaks these at configure (`RunSettings`); preparation reads the keys of `RunKeys` and refuses any other.

| key | rule |
|---|---|
| `inputSizes` | required; non-empty, positive, distinct |
| `phases` | required; `WARM` (`Phase.read`, also at preparation) |
| `metrics` | required; `TIME`, `ALLOCATION`; must hold `TIME`, no repeats (`Metric.read` in `:settings`) |
| `variants` | required, config writes it (its default lives there); distinct values of `fixed`, `notFixed`, `secure`, may be empty; absent: `missing_field`; an entry without its own takes it ([operations.md](operations.md#variants)) |
| `processRepetitions` | required; `>= 1` |
| `seed` | required |
| `harness` | optional; settings key table |
| `policy.onFailure` | required; `STOP`, `SKIP` |

## Selections

`providers.<provider>.<type>.<name>[@<group>]: {entry}`; entry fields `keySizes`, `inputSizes`, `key`, `parameters`, `operations`, `variants`, `providerDefaults`, `harness`, all optional.

| rule | value |
|---|---|
| entry key | algorithm before `@`, group after `@` or empty |
| `inputSizes` empty | `run.inputSizes` |
| `variants` absent | `run.variants`; values `fixed`, `notFixed`, `secure`, else `unknown_variant` |
| `key` | `algorithm`, `provider` and `backing` split off as the key source ([operations.md](operations.md#inputs-and-keys)), a non-blank string each, else `invalid`; `backing` `tee` or `strongbox`, else `invalid`; the rest is the spec tree |
| guide `keystore` | the guide item's keystore authorizations, carried by the selection to its `secure` cases only |
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

Type names match case-insensitively.

## Resolution

| rule | value |
|---|---|
| operations | entry `operations` narrows the type's list |
| expansion | provider x operation x keySize x inputSize x phase x variant; variant innermost: an item's two variants are adjacent |
| variant axis | the entry's asked paths that its setup-catalog row applies: a row's `variants` list (`[fixed, secure]` for key generation), `[fixed, notFixed]` for a row without one, `[fixed, secure]` for a type the catalog lacks (config skips such an entry first, `path_not_applicable`); a row's list of anything but distinct `fixed`, `notFixed`, `secure`: `invalid`; some dropped: dropped without a line (config notes each dropped path once per type); all dropped: the selection is rejected `path_not_applicable` |
| `secure` | kept only on a runtime with `android.security.keystore` and a selection with a guide `keystore` block; else removed, with one rejection when the entry's own `variants` asked for it or nothing is left: `not_supported: secure needs android.security.keystore ...` (a JVM), else `path_not_applicable: <provider>.<type>.<name> without a guide keystore block applies [..], [secure] dropped` |
| `key.backing` without a `secure` case | rejected `unused_setting: key.backing reaches no secure case` |
| backing on the case | only a `secure` case carries the key source's backing and the keystore block; `strongbox` joins the `p` tag, `tee` (the default) does not; a `secure` id ends `_secure` |
| keySize axis | only when the operation consumes key size and `keySizes` is set, else one null |
| inputSize axis | only when the operation consumes input, else one null |
| harness | `run.harness` merged with the entry's |
| metrics, seed | global values on every case |

| rejection | cause |
|---|---|
| `unsupported_operation: [..] for <type>, one of [..]` | entry operation not in the type |
| `key_parameters_and_key_sizes: set one; a key spec already fixes the size` | `key` and `keySizes` both set |
| `unused_setting: [key.algorithm/provider] ...` | a key source on an entry whose operations take no key |
| `unused_setting: [..] reaches no call of [..]` | `keySizes`, `inputSizes`, `key` or `parameters` that no operation consumes |
| `bind_failed: <path>: <detail>` | `key` or `parameters` tree fails to bind |
| Availability reason | provider cannot serve the name |

## Device availability

| rule | value |
|---|---|
| pairing | capture and trial share `capturedAtMillis`, else `mismatched_trial: capture <a>, trial <b>` |
| provider order | ascending `precedence` |
| lookup | registered algorithm or alias, case-insensitive |
| name with `/` | when not registered, checked as a transformation of the base Cipher service in the trial |
| reasons | `provider_not_installed`, `not_registered`, `not_tried`, `instantiation_fails: <error>`, `transformation_fails: <error>` |
| registered | the two `_fails` reasons mark the service registered: a selection's `secure` cases still run (a key born inside the provider fails the default-run trial); its other paths are rejected with the reason |
| `measuredKey` | the trial's `keyAlgorithm` and `fixedKeySize` for the service or transformation |

## Failures

| reason, prefixed `<caseId>: ` | stage |
|---|---|
| `KeyRecipe.Unavailable` reason | key plan |
| `key_generation_failed: <Exception>: <msg>` | key |
| `input_preparation_failed: <Exception>: <msg>` | input |
| `dry_run_failed: <Exception>: <msg>` | `once()` |

## Secure path

A `secure` case (key generation only) makes its key inside the case provider, `key/secure/`: Android's classes reached by reflection, never on a module's compile classpath.

| step | rule |
|---|---|
| alias | `cryptobench-<crc32 of the case id>`, one per case; every `cryptobench-` alias of the provider's own `KeyStore` service is deleted first (a killed process's) |
| spec | `KeyGenParameterSpec.Builder(alias, purposes)`: purposes OR'ed from `KeyProperties.PURPOSE_<NAME>` of the guide block, every other list `set<Name>(String...)`, `setKeySize(keySize)`, `setAlgorithmParameterSpec(<bound key spec>)`, else `ECGenParameterSpec(<block curve>)` (without one AndroidKeyStore makes a P-256 key under the Ed25519 and XDH names), `setIsStrongBoxBacked(true)` for `backing: strongbox`; no user authentication, no attestation |
| init and timed call | the spec is the case's key parameters: one init, then `generateKey()`/`generateKeyPair()` timed (KeyMint generation and the keystore's insert under the alias) |
| deletion | `PreparedCase.afterCall` deletes the alias after every timed call, outside the timed region (`Invocation.step`); the dry run's key is read back, then deleted |
| read-back | `KeyInfo` through the provider's own `SecretKeyFactory`, or the `KeyFactory` of the key's algorithm, else the first of the provider's `KeyFactory` services that reads it: `keyBits`, `securityLevel` `TEE`, `STRONGBOX`, `SOFTWARE` or `UNKNOWN` (API 31 `getSecurityLevel`; below it `isInsideSecureHardware` false `SOFTWARE`, true `UNKNOWN`); `backing` the requested `tee` or `strongbox`. Both are recorded in `resolvedParameters`, never compared |

| failure, prefixed `<caseId>: ` | cause |
|---|---|
| `not_supported: secure needs android.security.keystore ...` | a JVM |
| `api_too_low: <member> is absent on API <n>` | `<n>` the capture's `runtime.sdkInt`; a builder method or `KeyProperties` field this API lacks (`setIsStrongBoxBacked` below 28, `PURPOSE_AGREE_KEY` below 31) |
| `strongbox_unavailable: <provider> strongbox: <error>` | a `StrongBoxUnavailableException` in the failure's causes |
| `keystore_unsupported: <type> <algorithm>[/<keySize>]: <root error>` | the keystore refused the spec, the init or the generation |

`<Exception>: <msg>` comes from `FailureText`: key encodings removed, at most 200 characters, identity hashes dropped. Resolve rejections become skips with stage `preparation`. Outcome under `policy.onFailure`: [prepared.md](prepared.md#onfailure).
