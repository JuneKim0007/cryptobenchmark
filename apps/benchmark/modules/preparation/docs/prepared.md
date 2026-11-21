# prepared

What a run's preparation leaves: `skipped.yaml` and `prepared.yaml`, written by `RunnablePlan` (`apps/benchmark/modules/benchmark/docs/measure.md`) in the caller's output directory. Pipeline layout: `docs/results.md`. Stages: [prepare.md](prepare.md).

## onFailure

| policy | outcome |
|---|---|
| any | `skipped.yaml` always written; each failed case is added as it fails |
| `stop`, a rejection or a preparation skip | `StoppedOnFailureException` `stopped_on_failure: <n>` listing each, after every case was tried (host) or when the failing case ends (device) |
| `skip`, zero prepared cases | `nothing_prepared: every case was skipped, see <skipped.yaml>` |
| `skip`, some prepared | `prepared.yaml` holds the prepared cases |

## skipped.yaml

`schemaVersion: 2`; `skipped[]` of `{stage, provider?, type?, name?, caseId?, code, reason?}`: `caseId` when one case is meant, `code` the snake_case code, `reason` the detail after it. Same record as config's `skipped` (stage `config`, never a `caseId`); preparation writes stage `preparation`, the plan check `benchmark`, the end-to-end check `check`. A file of another version is refused (`unsupported_schema_version`).

## Case id

```
<type>_<algorithm>[@<group>]_<OPERATION>_<provider>[_k<keySize>][_i<inputSize>]_<PHASE>[_p<crc32>]_<variant>
```

| rule | value |
|---|---|
| characters | every non `[A-Za-z0-9]` character in each part becomes `-` |
| `p` tag | 8-hex CRC32 of canonical `keyParameters` and `parameters`, and the key source when it names an algorithm or a provider (`any` alone is not part of it); only when one of them is set |
| variant | last part, `fixed` or `notFixed`; the item's id is the case id without it |
| examples | `MessageDigest_SHA-256_DIGEST_SUN_i1024_WARM_fixed`, `Cipher_AES-GCM-NoPadding_ENCRYPT_SunJCE_k128_i1024_WARM_p81667fe4_notFixed` |
| `BenchmarkCase` defaults | phase WARM, metrics `{TIME}`, seed 0, variant `fixed` |

## prepared.yaml

`schemaVersion: 3`; written from the listing with each runnable case's listed fields, then each case's entry replaced by its prepared one, or removed when it could not be prepared. A process given cases by name edits only those entries; an entry still in its listed form is a case whose process ended before preparing it. Nothing reads it back to rebuild a case; the benchmark reads it to join Jetpack results by case id.

| key | holds |
|---|---|
| `generatedFrom.effective` | file name of the effective.yaml read |
| `generatedFrom.runId` | `runId` of that effective.yaml; absent when it has none |
| `run` | `seed`, `processRepetitions`, `harness` when non-empty |
| `cases[]` | one block per prepared case |

`cases[]` keys, in order:

| key | holds |
|---|---|
| `id`, `type`, `algorithm`, `provider`, `operation` | the case |
| `group` | when set |
| `chartGroup`, `chartGroupId` | which cases a chart may compare; from the service type, `Cipher` split by key kind (`secret` symmetric, `pair` asymmetric); `unidentified` (0) otherwise |
| `keySize`, `inputSize` | when set |
| `phase`, `variant`, `metrics` | the case axes; `variant` `fixed` or `notFixed` |
| `harness` | `run.harness` merged with the entry's; when non-empty |
| `key` | `kind` (`none`, `secret`, `pair`); secret and pair add `algorithm`, `provider`, `keySize?`, `parameters?`, and `encodedBytes` (secret length) or `pairs` (count) |
| `keyParameters`, `parameters` | spec trees that reached the generator and the call; when set |
| `specPerIteration` | `true` when the bound parameters vary |
| `input` | `kind` (`none`, `message`, `ciphertext`, `signedMessage`) and `bytes`; ciphertext adds `plaintextBytes` and `spec` (`carried`, `provider`, `none`) |
| `fingerprint` | first 8 hex of SHA-256 over the YAML dump of the case block without `fingerprint`, `perCall`, `resolvedParameters` and `from` |
| `perCall` | what one timed call does: `operation`, `initAndOperation` or `getInstanceInitAndOperation` ([operations.md](operations.md#variants)) |
| `resolvedParameters` | what the provider used, read back after the case's one call; always present, `{}` when nothing applies |
| `from` | the entry's `from` in effective.yaml as written, on listed and prepared entries; absent when the entry has none; outside `id` and `fingerprint` |

## resolvedParameters

Read by `parameter/resolve/ResolvedParameters` from the engine (`Invocation.engine`), the parameters it reports and the key. Spec classes and key interfaces are matched by type, never by algorithm name. A field that does not apply, or that the API does not expose, is omitted. Keys, in order:

| key | source |
|---|---|
| `mode`, `padding` | 2nd and 3rd part of `Cipher.getAlgorithm()` when it has three; a bare name leaves them out (the provider's choice is not exposed) |
| `ivBytes` | `GCMParameterSpec` IV; else `IvParameterSpec` or `getIV()`, kept only when a fresh instance fills in a different value on two inits or refuses to choose |
| `tagBits` | `GCMParameterSpec.tLen` |
| `digest`, `mgf1` | `OAEPParameterSpec` or `PSSParameterSpec`; `mgf1` only with `MGF1ParameterSpec` |
| `labelBytes` | `OAEPParameterSpec` `PSource.PSpecified` length; 0 for the empty default label |
| `keyBits` | the result key of a generate case, else the case key: secret encoded length, RSA modulus, EC field size, DSA or DH `p`; for a `secure` case `KeyInfo.getKeySize()` when the key has no encoding; absent for another key without encoding or key type |
| `backing`, `securityLevel` | a `secure` case: the requested backing and the level `KeyInfo` reports ([prepare.md](prepare.md#secure-path)) |
| `curve` | EC key: `ECGenParameterSpec` name from `AlgorithmParameters` of the key's algorithm (a name or an OID, by provider); else `field<bits>-<8 hex>` over p or m, a, b, G, n, h |

| case | outcome |
|---|---|
| a value the provider fills in identically on every init (a key-wrap integrity check value) | not an IV: no `ivBytes` |
| `Signature.getParameters()` unsupported | no engine parameters |
| a read-back that throws | the case is skipped: `parameters_unreadable: <exception>: <message>` |

No key bytes and no input bytes are written. Input bytes are reproducible from `seed` and size; keys are not (unseeded `SecureRandom`).

## Example

| file | role |
|---|---|
| `example/preparation_capture_example.yaml`, `preparation_trial_example.yaml`, `preparation_effective_example.yaml`, `guide.yaml` | inputs |
| `example/preparation_prepared_example.yaml`, `preparation_skipped_example.yaml` | expected outputs |

`ExampleFilesTest` prepares the example against the JVM and compares both outputs; `apps/benchmark/gradlew -p apps/benchmark :preparation:test -Dexamples.update` rewrites them and `tests/contracts/documents/guide.json` from `example/guide.yaml`.
