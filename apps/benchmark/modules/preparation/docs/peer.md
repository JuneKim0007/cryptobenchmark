# peer

`PeerEngine(capability).check(produced, consumer)`: whether another provider's engine, the consumer, takes a produced call's output. The end-to-end check's `crossProvider` oracle calls it once per peer provider with every parameter the call used (`Travel.USED`); interop calls `produced(case, recipe, key, consumer, Travel.MESSAGE_BORNE)`, which runs the producer first; its capability gives the availability a key use needs. Code under `src/main/kotlin/peer/`, one file per class below plus `Outcome` (verdict and label; a pass by use names it), `OutputBytes` (a call's output as bytes), `ProducedCall`, `Consumer`, `Travel`, `PeerCase` (seed 0, input 16), `PeerRefusal`; covered by `PeerRowsTest`, `KeyUseTest`, the cli `FailureClassifiersTest`.

## Procedure

| step | rule |
|---|---|
| produce | interop only: the producer's call once at its defaults; a failure `not_checkable` `producer_failed` |
| row | the produced operation's row in `PeerEngine.ROWS`; none: `not_checkable` `no_peer_check` |
| ready | the row's shape and input checks: `fail` `not_bytes`; `not_checkable` `no_engine_read_back`, `no_ciphertext_input`, `no_key_pair`, `no_signed_input`, `no_key` |
| setup | the consumer's instance, the key rebuilt by `PeerKey` (Keys below), the parameters from `PeerParameters`, init |
| consume | the consumer's call and the row's judgement of its result, inside one `Attempt` (a judge that throws fails as consume): `fail` `peer_differs`, `peer_rejects`; else `pass` |
| failure | an Exception or LinkageError of setup or consume goes through the `Outcomes` table; any other Error escapes |

## Outcomes

First matching rule wins. Stages: produce (the producer's own call), setup over an input key, setup over the output key a generator produced, consume.

| stage | exception | verdict |
|---|---|---|
| produce | any | `not_checkable` `producer_failed` |
| setup, output key | `PeerRefusal` `peer_key_rejected`, `InvalidKeyException`, `InvalidKeySpecException` | `fail` `peer_key_rejected` |
| setup, consume | `PeerRefusal` | `not_checkable` with its code |
| setup | `NoSuchAlgorithmException`, `NoSuchPaddingException`, `NoSuchProviderException` | `not_checkable` `peer_unavailable` |
| setup | `InvalidKeyException`, `InvalidKeySpecException` | `not_checkable` `peer_key_rejected` |
| setup | `InvalidAlgorithmParameterException` | `not_checkable` `peer_parameters_rejected` |
| setup | any other | `not_checkable` `peer_setup_failed` |
| consume | `NoSuchAlgorithmException`, `NoSuchPaddingException`, `NoSuchProviderException` | `not_checkable` `peer_unavailable` |
| consume | `GeneralSecurityException` | `fail` `peer_refused` |
| consume | any other | `not_checkable` `peer_error` |

## Keys

| rule | value |
|---|---|
| order | the consumer's instance first, then its key |
| secret key | raw bytes as a `SecretKeySpec` |
| public, private key | X.509 or PKCS#8 encoding through the consumer's KeyFactory under the key's name; its refusal is the consumer's |
| no factory under that name | the consumer's other KeyFactories by sorted name, then the first installed provider's under the key's name that rebuilds it; none: `PeerRefusal` `peer_unavailable` |
| no encoding | `PeerRefusal` `key_not_extractable` |

## Rows

| row | operations | consumer |
|---|---|---|
| `CipherRow` | ENCRYPT, DECRYPT | decrypts the ciphertext to the input, or the same ciphertext to the output |
| `SignatureRow` | SIGN, VERIFY | verifies the signature with the rebuilt public key; parameters only when the case binds them |
| `RecomputeRow` | DIGEST, COMPUTE_MAC, AGREE_KEY | recomputes the bytes; an agreement from the first pair's private and the last pair's public key |
| `KeyOutputRow` | GENERATE_KEY, GENERATE_KEY_PAIR | the output must be a secret key or key pair (`fail` `not_a_key`); the producer runs the key's use once with it (an agreement with the jca `PeerPair` as the other party), and the consumer takes that call through the use's row; its key setup is the output-key stage |

## Key use

| rule | value |
|---|---|
| catalogues | `algorithms/cipher.secret_catalogue.yaml`, `cipher.pair`, `signature.pair`, `mac.secret`, `agreement.peer`, entries in file order, read through document's `FamilyCatalogue` |
| build view | each entry as each provider's build sees it: `deviations.yaml` and provider-wide behaviours applied as the Python reader does; the build is the provider's on the capture's platform (`android-<sdk>`, `jdk-<major>`), else the nearest at or below, else its latest |
| key type | the generator's own entry in `keygen.none` or `keypairgen.none` (`KeyGenerator\|HmacSHA256` gives `HMAC`), its `key.type` on the producer's build; if no use has that type, the key's algorithm name (`getAlgorithm`) |
| entry | the first whose `key.type`, on both builds, equals the key type, case folded, and whose type and name the capability reports Available on both providers; first `algorithms/groups.yaml`'s exemplars of those families, then, only if none fits, catalogue order, each by type Signature, Cipher, Mac, KeyAgreement (an EC key: `Signature\|SHA256withECDSA`; X25519: `KeyAgreement\|X25519`) |
| operation | the first of the entry's `operations` words that begins the name of an operation `engine-operations.yaml` times for its type (`computeMac` COMPUTE_MAC, `agree` AGREE_KEY); `wrap` has none |
| reason | a `fail` or `not_checkable` by use ends `(use <type>\|<name> <OPERATION>)`; a `pass` by use carries `use <type>\|<name> <OPERATION>` |
| none | `not_checkable` `no_key_use`, naming the key types tried (a generator whose type no use has, such as `KeyPairGenerator\|XDH`, `EdDSA` or `ECDSA`) |
| case | seed 0, input 16, no bound parameters |
