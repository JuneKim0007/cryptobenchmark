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
| `Cipher.doFinal` into a preallocated buffer | ENCRYPT, DECRYPT |
| `update` + `sign` | SIGN |
| `update` + `verify`; false fails `verify_failed` | VERIFY |
| `Mac.doFinal` | COMPUTE_MAC |
| `MessageDigest.digest` | DIGEST |
| `doPhase` + `generateSecret` | AGREE_KEY |
| `generateKey`, `generateKeyPair` | GENERATE_KEY, GENERATE_KEY_PAIR |

| rule | value |
|---|---|
| measured generator init | spec: `init(spec)`; else keySize: `init(keySize)`; else provider default; no `SecureRandom` passed |
| Cipher re-init | per call when parameters vary or the provider refuses a second `doFinal`; refusing re-init with the same parameters fails `not_repeatable: ...; draw them with fresh(n)` |
| ENCRYPT spec pool | varying parameters: 256 specs drawn before timing, cycled `specs[n % size]` |
| other operations | call `next()` on the parameters once |
| `Invocation` | `perIteration` is timed; `once()` returns the exact result (Cipher output trimmed to bytes written) |
| `Invocations.of(prepared)` | the case's invocation; used by the host and device harness |

## Inputs and keys

| rule | value |
|---|---|
| message | `java.util.Random(seed).nextBytes(size)` |
| DECRYPT input | seeded message encrypted once; carries ciphertext and spec (provider `AlgorithmParameters` when no spec); round trip checked, `round_trip_failed` |
| VERIFY input | seeded message signed once and verified; carries message and signature |
| asymmetric cipher | encrypt with the first pair's public key, decrypt with its private key |
| key candidates | trial `keyAlgorithm` first, then names derived from the algorithm |
| Cipher derivation | part before `/`; `<base>_<n>` gives base and size `n`; part before `-` |
| Signature derivation | part after `with`, minus `inP1363Format`, `ECDSA` to `EC`; KeyAgreement `ECDH` to `EC` |
| generator provider | the case's provider, then all providers in precedence order; first with an available generator |
| DEVICE_DECIDES | secret `KeyGenerator` first, then a one-pair `KeyPairGenerator` |
| PEER_PAIRS | two key pairs |
| no generator | `no_key_generator: <KeyGenerator\|KeyPairGenerator>.<alg>`; `no_key_generator: <alg>` for DEVICE_DECIDES |
| recipe keySize | case keySize, else the size parsed from the name |
| entry `key` | keyed operations: goes to the key generator; GENERATE_KEY(_PAIR): the measured init spec |
| randomness | unseeded `SecureRandom()`; `DefaultKeyInitializer` unless a per-provider initializer is registered |
| `DefaultKeyInitializer` | spec: `init(spec, random)`; keySize: `init(keySize, random)`; else `KeyGenerator.init(random)`, `KeyPairGenerator` left uninitialised |

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
