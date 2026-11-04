# Signature

`grouping/signature.py` derives each item's signature at build, into its profile: `catalog/interchange.yaml` reads the canonical name (`catalog/algorithm-names.yaml`, probe aliases included), `catalog/resolved.py` the trial's digest and MGF1, the profile the key contract.

The signature is best effort and exists only to reduce model calls: it seeds `catalog/groups.yaml` offline (`../../tools/seed_groups.py`, reviewed before commit), shows the model its facts, and checks groups (gate C, static findings); it never places an item at run time ([grouping.md](grouping.md) Identified items).

| Component status | Meaning | Seed (`../../tools/seed_groups.py`) |
|---|---|---|
| `known` | read from the name, `resolved` or the key contract | a row when all are known |
| `convention` | a provider's habit nothing recorded confirms: PSS MGF1 and salt, PBE KDF, curve by key (EdDSA, XDH, ML-DSA), a missing key contract on a Cipher, Signature, Mac or KeyAgreement (`key: assumed`), a generator's consumer | a row stating it `(assumed)`; a group of two or more gets `convention_assumed` |
| `unknown` | nothing recorded fixes it, never the name's default: an uncatalogued name, a `name_conflict`, OAEP digest or MGF1 without `resolved`, a bare name's mode and padding, RSASSA-PSS parameters set at init, a generator's key contract (`key: asked`) | no row: the model decides |

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

- Seed: names of one family whose signatures, the key aside, are equal share a proposed row; the key contract splits a row at build, never in the catalog.
- A generator's `key` is its trial's: no attribute says whether the key it makes stays inside the provider.

- `keyMaterial` is the trial's `defaultRun.keyMaterial`, else `exportable` for `app_held` and `non_exportable` for `provider_held`, else `unknown`; a generator whose default run failed records nothing.
- `keyMaterial` is the one component where `unknown` decides: gate C refuses to join an unknown side to a known one; a generator whose key contract is unknown joins nothing (Generators).
- A screened-out generator group splits by `keyMaterial` too; no other screened-out group id changes.
- A model answer joins no group across a component both sides know (gate C).
- A model never joins a code-made group; it may join a catalog group whose members' known components agree with its own.
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
- The prompt is unchanged: the model sees only the `facts.key.key` it already reads.
