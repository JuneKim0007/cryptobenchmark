# operations

What each operation consumes, its timed call, inputs, keys and parameter trees. Stages and failures: [prepare.md](prepare.md).

## Operations

| operation | key shape | keySize | key | parameters | input |
|---|---|---|---|---|---|
| ENCRYPT | DEVICE_DECIDES | yes | yes | `Cipher.init` spec | yes |
| DECRYPT | DEVICE_DECIDES | yes | yes | `Cipher.init` spec | ciphertext |
| SIGN | PAIR | yes | yes | `Signature.setParameter` | yes |
| VERIFY | PAIR | yes | yes | `Signature.setParameter` | signed message |
| COMPUTE_MAC | SECRET | yes | yes | `Mac.init(key, spec)` | yes |
| DIGEST | NONE | no | no | no | yes |
| GENERATE_KEY, GENERATE_KEY_PAIR | NONE | measured init | measured init | no | no |
| AGREE_KEY | PEER_PAIRS | yes | yes | `KeyAgreement.init(key, spec)` | no |
| TYPE_DEFAULT | DEVICE_DECIDES | yes | yes | yes | yes; invocation returns null |

| timed call | operation |
|---|---|
| `doFinal` into a preallocated buffer, with `Cipher.init` before it when the [variant](#variants) says | ENCRYPT, DECRYPT |
| `update` + `sign` | SIGN |
| `update` + `verify`; false fails `verify_failed` | VERIFY |
| `Mac.doFinal` | COMPUTE_MAC |
| `MessageDigest.digest` | DIGEST |
| `doPhase` + `generateSecret` | AGREE_KEY |
| `generateKey`, `generateKeyPair` | GENERATE_KEY, GENERATE_KEY_PAIR |

| rule | value |
|---|---|
| measured generator init | spec: `init(spec)`; else keySize: `init(keySize)`; else provider default; no `SecureRandom` passed |
| Cipher init | inside the timed call when the variant's `perCall` holds it; ENCRYPT takes the next pooled spec, DECRYPT the ciphertext's; a provider refusing a second init fails `not_repeatable: ...; draw them with fresh(n)`, one refusing a second `doFinal` without init `not_repeatable: ...` naming the catalog |
| fresh IV | an IV or nonce from `fresh(n)` in a test-set override is drawn before timing; without one the provider draws it inside the timed init |
| ENCRYPT spec pool | varying parameters: 256 specs drawn before timing, cycled `specs[n % size]` |
| other operations | call `next()` on the parameters once |
| `Invocation` | `perIteration` is timed; `once()` returns the exact result (Cipher output trimmed to bytes written); `again()` replays the last call with the parameters it drew, on a new instance when the call re-inits; `perCall` what the timed call redoes |
| `Invocations.of(prepared)` | the case's invocation, every definition handed the setup catalog; used by preparation's dry run and the host and device harness |

## Variants

Each item is measured once per path its entry's `variants` keeps ([prepare.md](prepare.md#resolution)), each its own case. Setup outside the call runs once, before the timer, in `Invocations.of`; keys, inputs, spec pools and the output buffer are built before it too.

| material | across an item's two variants |
|---|---|
| message bytes | equal: `InputBytes.of(run.seed, size)` |
| keys | unseeded `SecureRandom`, made once per key recipe per process: equal in one process, different when each variant runs in its own |
| `fresh(n)` spec pools | unseeded `SecureRandom`, drawn per case: different bytes, same shape |
| DECRYPT ciphertext, VERIFY signature | made per case from that case's key and spec |

| variant | timed call |
|---|---|
| `fixed` | the setup the API lets a call keep, kept: what the catalog row below still does per call |
| `notFixed` | `getInstance` + init + operation every call, for every row |

Catalog: `algorithms/setup-catalog.yaml`, read through `:catalogue` `EngineRows` by `operation/SetupCatalog` (the build puts it beside the class) and by config's `entry/EngineCatalog`; a type without a row is a `not_in_catalogue` skip; each row cites the JCA API contract it rests on. No engine or mode name is in code.

| engine type, mode | `fixed` per call (`perCall`) | contract |
|---|---|---|
| MessageDigest | operation (`operation`) | `digest()` resets the digest |
| Mac | operation | `doFinal()` resets the Mac to its state after `init(key)` |
| Mac named `...GMAC` | init with the next fresh IV + operation | a GMAC nonce must not repeat under one key: its IV role lives `perUse` with `rule: unique`, whatever `lifecycle.reset` says |
| Signature | operation after one init | `sign()`, `verify()` reset to the state after `initSign`/`initVerify` |
| KeyAgreement | operation after one init | `generateSecret()` resets to the state after `init` |
| Cipher ECB, NONE | operation | `doFinal()` resets the cipher to its state after init |
| Cipher CBC, PCBC, CTS, CFB, OFB, CTR | init with the next fresh IV + operation (`initAndOperation`) | an IV must not repeat under one key |
| Cipher GCM, CCM | init with the next fresh IV + operation | a nonce must not repeat under one key; the provider refuses a reused one |
| Cipher, other mode | init + operation | unknown mode |
| Cipher without a mode (stream or provider default) | operation when the initialised cipher has no IV, else init + operation | as above |
| KeyGenerator, KeyPairGenerator | `variants: [fixed, secure]`: `generateKey()`/`generateKeyPair()` after one init, `secure` with a KeyGenParameterSpec ([prepare.md](prepare.md#secure-path)); a row giving anything but `operation` is refused (`not_supported`) | the generation is the work |
| a type not in the catalog | paths `[fixed, secure]`: `fixed`, operation | |

| rule | value |
|---|---|
| `perCall` labels | `operation`, `initAndOperation`, `getInstanceInitAndOperation`; in `prepared.yaml` per case |
| DECRYPT `initAndOperation` | init with the ciphertext's IV; decrypting may repeat one |
| allocation | each variant is its own case with its own `allocationCount` |
| order on a device | items shuffled by `run.orderSeed`, variants interleaved per item, each in its own process: [device-session.md](../../../../../docs/device-session.md#variants) |

## Inputs and keys

| rule | value |
|---|---|
| message | `java.util.Random(seed).nextBytes(size)` |
| DECRYPT input | seeded message encrypted once; carries ciphertext and spec (provider `AlgorithmParameters` when no spec); round trip checked, `round_trip_failed` |
| VERIFY input | seeded message signed once and verified; carries message and signature |
| asymmetric cipher | encrypt with the first pair's public key, decrypt with its private key |
| key | entry `key.algorithm`, else the trial's `keyAlgorithm` and `fixedKeySize` (the size kept when the written name is the measured one): discovery's `KeyCandidates` is the one naming rule; neither: `no_measured_key: <type>.<alg>` |
| generator provider | entry `key.provider`: `same` (default) the case's provider; `any` the case's provider, then all providers in precedence order, the first with an available generator; else the named one; no other provider is tried |
| interop check | the key shared by both members: the producer's provider, then all providers in precedence order ([interop.md](interop.md)) |
| DEVICE_DECIDES | secret `KeyGenerator` first, then a one-pair `KeyPairGenerator` |
| PEER_PAIRS | two key pairs |
| no generator | `no_key_generator: <KeyGenerator\|KeyPairGenerator>.<alg> in <provider>`; `no_key_generator: <alg> in <provider>` for DEVICE_DECIDES; `<provider>` is `any provider` under `any` |
| recipe keySize | case keySize, else the size parsed from the name |
| entry `key` | keyed operations: goes to the key generator; GENERATE_KEY(_PAIR): the measured init spec |
| randomness | unseeded `SecureRandom()` |
| `KeyInitializer` | spec: `init(spec, random)`; keySize: `init(keySize, random)`; else `KeyGenerator.init(random)`, `KeyPairGenerator` left uninitialised |

## Parameter trees

| form | means |
|---|---|
| `{class, arguments}` | public constructor, chosen by arity, then coercion |
| `{field: pkg.Class.NAME}` | public static field; its class must pass the policy |
| `fresh(n)` | `n` random bytes per evaluation |
| other literal | value; Int and Long exact, `BigInteger`, a list of `-128..255` as `byte[]` |

| rule | value |
|---|---|
| allowed classes | `BindPolicy.standard()`: subtypes of `AlgorithmParameterSpec`, `PSource`, `BigInteger` |
| root | must evaluate to `AlgorithmParameterSpec` |
| map errors | other keys: `unknown keys [...]`; neither class nor field: `a map needs 'class' or 'field'` |
| error path | e.g. `parameters.arguments[2]` |
| `varies` | the tree contains `fresh()` |
