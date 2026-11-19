# peer

`PeerEngine.check(produced, consumer)`: whether another provider's engine, the consumer, takes a produced call's output. The end-to-end check's `crossProvider` oracle calls it once per peer provider. Code under `src/main/kotlin/peer/`; covered by `PeerRowsTest`, the cli `FailureClassifiersTest`.

## Procedure

| step | rule |
|---|---|
| row | the produced operation's row in `PeerEngine.ROWS`; none: `not_checkable` `no_peer_check` |
| ready | the row's shape and input checks: `fail` `not_bytes`; `not_checkable` `no_engine_read_back`, `no_ciphertext_input`, `no_key_pair`, `no_signed_input`, `no_key` |
| setup | the consumer's instance, the key rebuilt by `PeerKey`, the parameters from `PeerParameters`, init |
| consume | the consumer's call; its result judged by the row: `fail` `peer_differs`, `peer_rejects`; else `pass` |
| failure | an Exception or LinkageError of setup or consume goes through the `Outcomes` table; any other Error escapes |

## Outcomes

| stage | exception | verdict |
|---|---|---|
| setup | `PeerRefusal` | `not_checkable` with its code |
| setup | `InvalidKeyException` | `not_checkable` `peer_key_rejected` |
| setup | `InvalidAlgorithmParameterException` | `not_checkable` `peer_parameters_rejected` |
| setup | `NoSuchAlgorithmException`, `NoSuchPaddingException` | `not_checkable` `peer_unavailable` |
| setup | any other | `not_checkable` `peer_setup_failed` |
| consume | `GeneralSecurityException` | `fail` `peer_refused` |
| consume | any other | `not_checkable` `peer_error` |

## Rows

| row | operations | consumer |
|---|---|---|
| `CipherRow` | ENCRYPT, DECRYPT | decrypts the ciphertext to the input, or the same ciphertext to the output |
| `SignatureRow` | SIGN, VERIFY | verifies the signature with the rebuilt public key; parameters only when the case binds them |
| `RecomputeRow` | DIGEST, COMPUTE_MAC, AGREE_KEY | recomputes the bytes; an agreement from the first pair's private and the last pair's public key |
| `KeyOutputRow` | GENERATE_KEY, GENERATE_KEY_PAIR | rebuilds a key pair, the public half to the same encoding; a secret key `not_checkable` `no_peer_check` |
