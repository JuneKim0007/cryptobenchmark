# Entry paths and key source

Two per-entry settings of a test set, beside the keys of [config.md](config.md#testsetsyaml); resolved into effective.yaml as [generated.md](generated.md#entry-values) says.

## Variants

`variants`: the execution paths an entry is measured along, a list of `fixed` (setup the API lets a call keep stays outside the timed call), `notFixed` (instance and init every call), `secure` (the hardware-isolated key path).

| rule | value |
|---|---|
| precedence | `overrides[].set.variants` > the include's `variants` > `run.variants` > `[fixed, notFixed, secure]`; within overrides and within includes the most specific, then the later, wins |
| invalid | anything but a non-empty list of distinct names (unknown name, scalar, `[]`, a repeat): `[fixed]` and one `variants_fallback` notice in report.yaml |
| `secure` | not built: dropped from every entry and from `run.variants` in effective.yaml; one `secure_path_unavailable` notice when an entry asks for it; an entry left with no path is skipped `secure_path_unavailable` |
| effective.yaml | each entry records its resolved list |
| a type's paths | preparation keeps the asked paths its setup-catalog row applies ([prepare.md](../../preparation/docs/prepare.md#resolution)) |

```yaml
include:
  - {type: Cipher, name: AES/GCM/NoPadding, variants: [fixed]}
  - {type: KeyGenerator, name: AES}
overrides:
  - match: {type: Mac, name: HmacSHA256}
    set: {variants: [fixed, notFixed]}
```

## Key source

`key.algorithm` and `key.provider`, beside a key's spec tree (`class` + `arguments`, or `field`).

| key | default | rule |
|---|---|---|
| `algorithm` | the trial's measured key (`keyAlgorithm`) | a JCA name the key provider registers as a `KeyGenerator` or `KeyPairGenerator` in the inventory (names folded through `algorithms/algorithm-names.yaml`), else skipped `no_key_generator` |
| `provider` | `same`: the entry's own provider | `same` or an inventory provider name, else skipped `provider_not_installed`; another provider's generator is used only when named here |
| either | | a non-blank string, else `invalid: key` |

A written source joins the case id's `p` tag ([prepared.md](../../preparation/docs/prepared.md)). A spec class a provider refuses is the trial's and preparation's to report, as for any spec.

```yaml
overrides:
  - match: {provider: SunJCE, type: Cipher, name: "RSA/*"}
    set: {key: {provider: SunRsaSign}}
  - match: {type: Signature, name: SHA256withECDSA}
    set: {key: {algorithm: EC, class: java.security.spec.ECGenParameterSpec, arguments: [secp256r1]}}
```
