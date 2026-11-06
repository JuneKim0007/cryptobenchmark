# requirements

The third trial level: what each registered service requires, measured by running it. File map: [index.md](index.md).

Level 3 names no algorithm: each variation is built from a spec a provider accepted, and digests come from the capture.

| type | facts |
|---|---|
| Cipher | `defaultInit`, `blockBytes`, `specClasses` (accepted, and accepted yet ignored), `ivBytes`, `tagBits`, `keyBytes`, `keyBits`, `foreignKeys`, `inputBytes` with `outputBytes` (input:output lengths) and `maxInputBytes`, `deterministicFixed`, `deterministicGenerated`, `reuseGuard` (the same Cipher re-initialised with the key and nonce it just used, as an app sees it; beside it `newInstance`, a second Cipher, and `spi`, the provider's own SPI wrapped in one Cipher, or `not registered under this name`), `roundTrip`, `decryptWithoutParameters`, `tamper`, `aad`, `effects`; a cipher that only wraps: `wrapRoundTrip` |
| Signature | `signatureBytes`, `deterministic`, `signatureBytesRange`, `parameters`, `verifies`, `tamperedSignature`, `tamperedMessage`, `inputBytes`, `setParameter`, `keyBits`, `foreignKeys` |
| Mac | `macBytes`, `lengthBeforeInit`, `deterministic`, `keyBytes`, `withoutInit`, `ivSpec`, `inputBytes`, `cloneable`, `foreignKeys` |
| MessageDigest | `digestBytes`, `lengthDeclared`, `deterministic`, `inputBytes`, `cloneable`, `emptyInputPrefix` |
| KeyAgreement | `secretBytes`, `bothSidesAgree`, `deterministic`, `withoutPeer`, `secretAsKey`, `keyBits`, `peerOfOtherSize`, `foreignKeys` |
| KeyGenerator, KeyPairGenerator | read from the default run: `defaultBits`, `keyMaterial`, `keyFormat`, `sizes` |
| SecretKeyFactory | `fromPassword`, or `fromPasswordRefused` and `rawKeyBytes` |
| any other type | the record with `no_call_for_type` |

| rule | value |
|---|---|
| key order | `KeyNames`, then every registered generator or factory name the service's name contains, longest first; per name the service's provider, then the others: `KeyGenerator`, `KeyPairGenerator`, `SecretKeyFactory` with `PBEKeySpec`; last `SecretKeySpec` of 16, 32, 24, 8 bytes |
| spec order | a digest's message is the longest of 64, 32, 16, 1, 0 bytes it takes; no spec, then each `ParameterSpecs` candidate; the first key, spec and input that run are `runWith`; a cipher that refuses every input but wraps runs with `operation: wrap` |
| sweeps | the whole call, not only the init: `ivBytes` 0..32, `tagBits` 0..256 by 8, `keyBytes` 1..64, Mac keys 1..64, 96, 128, 160 |
| `keyBits` | RSA and EC keys only: 224, 256, 384, 512, 521, 1024, 2048; other pairs cost a parameter generation per size |
| one key cache | `DefaultKeys`, one per run across levels 2 and 3, keyed by generating provider, name and size; a refused generation is cached too; counts in `keyCache` |
| one call per fact | `FactSheet.measure` catches any `Throwable` per fact; a whole call failing is `probe_failed`; nothing aborts the file |
| error text | `ErrorText`: whitespace folded, hex or decimal runs of 32, colon-separated hex of 9 bytes and base64 runs of 48 characters become `<removed>`, then capped at 200 |
| keystore-born | `KeyOrigin`: a provider none of whose generators or factories ran, with at least one service refusing a key, has `keystore_born_key` and the condition `keystore-born key` on each refusing service; a cipher that encrypts on a public key and refuses the private one counts as refusing; a service of that provider which runs on a software key stays `runnable` |
| API guard | `ChaCha20ParameterSpec` by name only; no class newer than API 26 is referenced |
| aliases | per declared alias: `classRun`, `sameClass`, `behaviour` (the same call under the alias gives the same result as under the service's name; a generator or factory has none), `ownNameKey` when the service ran on a non-password key and a factory makes a password key under the alias's name, with whether it ran |

## File

Measured per service on this device; never a catalogue fact. Read on the host through `REQUIREMENTS_DOC` (`apps/perf-repair/src/perfrepair/data_handler/inbound/probe/_requirements.py`).

| field | type | description |
|---|---|---|
| `schemaVersion` | int | `1` |
| `capturedAtMillis`, `deviceClockMillis` | long | as in the capture |
| `millis` | long | level 3's time on the device |
| `keyCache` | object | `generated`, `refused`, `reused`, `generationMillis` over levels 2 and 3 |
| `services` | list | one record per captured service, plus one per declared transformation that instantiates |

## services[]

| field | type | description |
|---|---|---|
| `provider`, `type`, `algorithm` | string | the service |
| `transformationOf` | string | the service a declared transformation belongs to |
| `className`, `classRun` | string | class the capture names; class an instance really has |
| `status` | string | `runnable`, `not_runnable`, `no_call` |
| `reason` | string | present unless runnable: `no_call_for_type`, `provider_not_installed`, `instantiation_failed`, `instance_refused` (registered, yet `getInstance` refuses), `no_key`, `key_refused`, `keystore_born_key`, `generation_refused`, `parameters_unknown`, `operation_refused`, `probe_failed` |
| `detail` | string | the refusal, through `ErrorText` |
| `conditions` | list | `keystore-born key` |
| `key` | object | `source`, `algorithm`, `class`, `provider`, `bits` of the key it ran on |
| `runWith` | object | `operation`, `providerGenerates`, `spec`, `inputBytes` it ran with |
| `keysTried` | list | keys refused before that, each with `refused` |
| `facts` | map | the table above; a fact whose call threw holds `error` |
| `aliases` | list | `name`, `classRun`, `sameClass`, `behaviour`, `ownNameKey` |
| `millis` | long | time on this record |
