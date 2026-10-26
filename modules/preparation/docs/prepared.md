# prepared

What preparation writes: `skipped.yaml` and `prepared.yaml` in the caller's output directory. Pipeline layout: `docs/results.md`. Stages: [prepare.md](prepare.md).

## onFailure

| policy | outcome |
|---|---|
| any | `skipped.yaml` always written |
| `stop`, any skip | `StoppedOnFailureException` `stopped_on_failure: <n>` listing each skip; `prepared.yaml` not written |
| `skip`, zero prepared cases | `nothing_prepared: every case was skipped, see <skipped.yaml>` |
| `skip`, some prepared | `prepared.yaml` written from the prepared cases |

## skipped.yaml

`schemaVersion: 1`; `skipped[]` of `{stage, provider, type, name, reason}`. Same record shape as config's `skipped` (stage `config`); preparation writes stage `preparation`.

## Case id

```
<type>_<algorithm>[@<group>]_<OPERATION>_<provider>[_k<keySize>][_i<inputSize>]_<PHASE>[_p<crc32>]
```

| rule | value |
|---|---|
| characters | every non `[A-Za-z0-9]` character in each part becomes `-` |
| `p` tag | 8-hex CRC32 of canonical `keyParameters` and `parameters`; only when either is set |
| examples | `MessageDigest_SHA-256_DIGEST_SUN_i1024_WARM`, `Cipher_AES-GCM-NoPadding_ENCRYPT_SunJCE_k128_i1024_WARM_p81667fe4` |
| `BenchmarkCase` defaults | phase WARM, metrics `{TIME}`, seed 0 |

## prepared.yaml

`schemaVersion: 1`; overwritten each run. Nothing reads it back to rebuild a case; the benchmark reads it to join Jetpack results by case id.

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
| `chartGroup`, `chartGroupId` | which cases a chart may compare; from the service type, `Cipher` split by name; `unidentified` (0) otherwise |
| `group`, `keySize`, `inputSize` | when set |
| `phase`, `metrics` | the case axes |
| `harness` | `run.harness` merged with the entry's; when non-empty |
| `key` | `kind` (`none`, `secret`, `pair`); secret and pair add `algorithm`, `provider`, `keySize?`, `parameters?`, and `encodedBytes` (secret length) or `pairs` (count) |
| `keyParameters`, `parameters` | spec trees that reached the generator and the call; when set |
| `specPerIteration` | `true` when the bound parameters vary |
| `input` | `kind` (`none`, `message`, `ciphertext`, `signedMessage`) and `bytes`; ciphertext adds `plaintextBytes` and `spec` (`carried`, `provider`, `none`) |
| `fingerprint` | first 8 hex of SHA-256 over the YAML dump of the case block without `fingerprint` |

No key bytes and no input bytes are written. Input bytes are reproducible from `seed` and size; keys are not (unseeded `SecureRandom`).

## Example

| file | role |
|---|---|
| `example/preparation_capture_example.yaml`, `preparation_trial_example.yaml`, `preparation_effective_example.yaml` | inputs |
| `example/preparation_prepared_example.yaml`, `preparation_skipped_example.yaml` | expected outputs |

`ExampleFilesTest` prepares the example against the JVM and compares both outputs; `./gradlew :preparation:test -Dexamples.update` rewrites them. `-Dtrial=<file>` points `KeyAlgorithmContractTest` at a device trial.
