# keystore trial

Level 4 of the trial ([probe.md](probe.md)): whether a keystore provider makes each catalogue key size or curve on each hardware path. File fields: [security_contract.md](security_contract.md#keystore).

| rule | value |
|---|---|
| generators | `KeyGenerator` and `KeyPairGenerator` records labelled `keystore_born_key`, matched case-folded by name or a captured alias to a catalogue entry with a `keystore` block (`algorithms/keygen.none_catalogue.yaml`, `algorithms/keypairgen.none_catalogue.yaml`, read through `:document`'s `FamilyCatalogue`) |
| rows | each `trialKeySizes` value (`setKeySize`), else each `trialCurves` value (`ECGenParameterSpec`), else one row with the block alone; each on `tee`, then `strongbox` |
| spec | `KeyGenParameterSpec.Builder(alias, purposes)` built by reflection as preparation's `KeystoreSpec` builds it; `setIsStrongBoxBacked(true)` on `strongbox` |
| alias | `cryptobench-trial-<n>`, fresh per row; deleted after each row; leftovers with that prefix swept before a provider's first row (preparation's sweep of `cryptobench-` also removes them) |
| StrongBox | the device's `android.hardware.strongbox_keystore` feature, read through `ActivityThread.currentApplication()`; declared absent: each `strongbox` row is `strongbox_unavailable` without a generation; unreadable: tried |
| refusal | a builder member this API lacks `api_too_low`; `StrongBoxUnavailableException` in the cause chain `strongbox_unavailable`; any other failure `keystore_unsupported: <type> <alg>[/<size or curve>] <backing>: ` and the innermost cause |
| no keystore classes | the section is `absent: not_supported: ...` (every host JVM) |
| cost | one generation per row, timed in `millis`: StrongBox RSA-2048 ≈ 8 s; TEE RSA-4096 several seconds; a refusal returns at once |
| consumer | configure: a refused row is a config skip with its `error` (`apps/benchmark/modules/config/docs/generated.md`) |
