# Entry paths and key source

Two per-entry settings of a test set, beside the keys of [config.md](config.md#testsetsyaml); resolved into effective.yaml as [generated.md](generated.md#entry-values) says.

## Variants

`variants`: the execution paths an entry is measured along, a list of `fixed` (setup the API lets a call keep stays outside the timed call), `notFixed` (instance and init every call), `secure` (key generation inside a provider that keeps its keys, AndroidKeyStore).

| rule | value |
|---|---|
| precedence | `overrides[].set.variants` > the include's `variants` > `run.variants` > `[fixed, notFixed, secure]`; within overrides and within includes the most specific, then the later, wins |
| invalid | anything but a non-empty list of distinct names (unknown name, scalar, `[]`, a repeat): `[fixed]` and one `variants_fallback` notice in report.yaml |
| `secure` | kept for `KeyGenerator` and `KeyPairGenerator` entries and in `run.variants`; dropped from every other entry with one `secure_path_unavailable` notice; an operation entry left with no path is skipped `secure_path_unavailable` |
| a generator the trial cannot call | (its key is born inside the provider) an entry asking `secure` is written `variants: [secure]`; without `secure` it stays a `not_runnable` skip |
| `notFixed` on key generation | one run-level notice `path_not_applicable: key generation takes fixed and secure; notFixed skipped for N entries`, N the generator entries asking `notFixed` |
| effective.yaml | an entry records its resolved list only when an override or include asked for one; otherwise it has no `variants` and `run.variants` applies |
| a type's paths | preparation keeps the asked paths its setup-catalog row applies ([prepare.md](../../preparation/docs/prepare.md#resolution)); a dropped path is noted only when the entry asked for it |

```yaml
include:
  - {type: Cipher, name: AES/GCM/NoPadding, variants: [fixed]}
  - {type: KeyGenerator, name: AES}
overrides:
  - match: {type: Mac, name: HmacSHA256}
    set: {variants: [fixed, notFixed]}
```

## Key source

`key.algorithm`, `key.provider` and `key.backing`, beside a key's spec tree (`class` + `arguments`, or `field`).

| key | default | rule |
|---|---|---|
| `algorithm` | the trial's measured key (`keyAlgorithm`) | a JCA name the key provider registers as a `KeyGenerator` or `KeyPairGenerator` in the inventory (names folded through `algorithms/algorithm-names.yaml`), or one of that generator's inventory `aliases` (an OID too), else skipped `no_key_generator` |
| `provider` | `same`: the entry's own provider | `same`; `any`: the entry's own provider, then every inventory provider in order, the first with the generator (none: skipped `no_key_generator`); or an inventory provider name, else skipped `provider_not_installed`; another provider's generator is used only when named here or under `any` |
| `backing` | `tee` | where a `secure` key is born: `tee` or `strongbox`, else skipped `invalid: key.backing`; reaches only the entry's `secure` cases, and an entry with none is rejected `unused_setting` |
| each | | a non-blank string, else `invalid: key` |

A written `algorithm`, provider name or `backing: strongbox` joins the case id's `p` tag; `any` alone and `tee` do not ([prepared.md](../../preparation/docs/prepared.md)). The provider used is prepared.yaml's `key.provider`. A spec class a provider refuses is the trial's and preparation's to report, as for any spec.

```yaml
overrides:
  - match: {type: Cipher, name: "RSA/*"}
    set: {key: {provider: any}}
  - match: {type: Signature, name: SHA256withECDSA}
    set: {key: {algorithm: EC, class: java.security.spec.ECGenParameterSpec, arguments: [secp256r1]}}
  - match: {provider: AndroidKeyStore, type: KeyGenerator, name: AES, group: sb}
    set: {keySizes: [128], key: {backing: strongbox}}
```
