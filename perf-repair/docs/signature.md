# Signature

`grouping/signature.py` derives each item's signature at build, into its profile: `catalog/interchange.yaml` reads the canonical name (`catalog/algorithm-names.yaml`, probe aliases included), `grouping/resolved.py` the trial's digest and MGF1, the profile the key contract.

| Component status | Meaning | Item |
|---|---|---|
| `known` | read from the name, `resolved` or the key contract | grouped by code when all are known |
| `convention` | a provider's habit nothing recorded confirms: PSS MGF1 and salt, PBE KDF, curve by key (EdDSA, XDH, ML-DSA), a missing key contract on a Cipher, Signature, Mac or KeyAgreement (`key: assumed`), a generator's consumer | grouped by code; the group of two or more gets `convention_assumed` |
| `unknown` | nothing recorded fixes it, never the name's default: an uncatalogued name, a `name_conflict`, OAEP digest or MGF1 without `resolved`, a bare name's mode and padding, RSASSA-PSS parameters set at init, a generator's key contract (`key: asked`) | asked |

| Rule key (`interchange.yaml`) | Reads |
|---|---|
| `set` | a component from the name; `$group` is a group of `match` |
| `resolved` | from the trial; missing with no `set` value is `unknown` |
| `convention`, `unknown` | as the statuses above |
| engine `defaults` | what no rule contradicts |
| engine `key` | `none` no key; `assumed`, `asked`: what a missing key contract means |

| Engine type | Splits |
|---|---|
| Cipher | base, mode, padding, digest, mgf1, wrap, passwordBased, kdf, key |
| Signature | scheme, digest, mgf1, salt, curve, encoding, prehashed, key |
| Mac | construction, digest, passwordBased, kdf, key |
| MessageDigest | function |
| KeyAgreement | algorithm, curve, key |
| KeyGenerator, KeyPairGenerator | function, consumer, key, keyMaterial |

- Group: an item not screened out with a decided signature is grouped by family and the signature's name and value pairs, so `known` and `convention` of one value share a group; id, description and rules as in [grouping.md](grouping.md) Code-made groups.
- A generator's `key` is its trial's: no attribute says whether the key it makes stays inside the provider, and on the API 30 capture the model split 8 generators on exactly that.

- `keyMaterial` is the trial's `defaultRun.keyMaterial`, else `exportable` for `app_held` and `non_exportable` for `provider_held`, else `unknown`; a generator whose default run failed records nothing.
- `keyMaterial` is the one component where `unknown` decides: gate C refuses to join an unknown side to a known one; a generator whose key contract is unknown joins nothing (Generators).
- A screened-out generator group splits by `keyMaterial` too; no other screened-out group id changes.
- A model answer joins no group across a component both sides know (gate C).
- A model never joins a code-made group: an asked item whose function a code-made group has stays in its own model group, a false split and no false join.
- Evidence, API 30 capture: of Haiku's 98 model groups, code makes 69 exactly and leaves the 29 others asked with no known component differing; neither side joins what the other split. The rules were written after that run, so this is consistency, not an independent test.
- Asked items, before → after, before the generator rule: JDK 17 155 → 28, JDK 21 162 → 28, JDK 25 176 → 36, Android 36 119 → 23, API 30 196 → 46; what stayed is generators (`key: asked`), OAEP without `resolved` and `name_conflict` names. With it, on the runtime fixtures, whose trials have no `keyFormat` so every generator is alone: 1, 1, 1, 0.
- Decided: a password-based name's derived key length (`_128`/`_256`, `128BIT`) is the `derivedBits` component and splits, because the provider derives the key from the name; a key size the call passes (`AES_128/...`) does not split.

## Generators

`grouping/build/key_contract.py`, from the trial's `defaultRun` and its `triedKeys` (each other size asked; a refused one made no key) and `catalog/key-contract.yaml` `generatedKeyFormats`:

| the produced key (a pair: its private key) | `keyContract` |
|---|---|
| `keyMaterial: non_exportable` (`getEncoded()` null), any format | `provider_held` |
| `exportable` with the standard format: `RAW` for KeyGenerator, `PKCS#8` for KeyPairGenerator | `app_held` |
| any other format or none, a run that failed or did not run, sizes whose keys disagree | `unknown` |

- Cross-check: the same provider's consumers of that key algorithm (a run whose `keyAlgorithm` is the generator's name; a run that failed names none, so any consumer of the key's kind counts), by their key attributes; one known contract that differs makes it `unknown` with `keyContractConflict` and a `key_contract_conflict` finding in `checks.json`.
- `unknown` joins no group: a code-made group of one (`screen/groups.py`), and gate C refuses a model answer that joins it or joins a group holding it; the failure is a missing option, never a swap that moves a key out of its provider.
- The prompt is unchanged: the model sees only the `key:` line it already reads.
