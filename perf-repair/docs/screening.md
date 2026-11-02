# Screening

## Statuses

| Status | Meaning |
|---|---|
| `broken` | a `crypto` row says `deprecated`, or a `components` rule matches the transformation |
| `platform_deprecated` | a `platform` row for the item's provider applies and the app's targetSdk is at or above its `deprecatedApi` |
| `accepted` | a `crypto` row says `accepted` and nothing above applies |
| `unknown` | no row applies, or the name is a `name_conflict` |

## Precedence

`broken` > `platform_deprecated` > `accepted` > `unknown`; the first that applies is the verdict.

## Lookup

- key: the engine type and the canonical name from `src/perfrepair/catalog/names.py`, probe aliases included; every spelling of a name gets one verdict.
- key size: dropped; `AES_256/GCM/NoPadding` is looked up as `AES/GCM/NoPadding`.
- components: a transformation `base/mode/padding` is `broken` when its base or its mode is listed.
- nominal mode: a mode the names catalog maps another mode onto for a base (`modeSynonyms`) never matches that base; `RSA/ECB/*` is not ECB.
- platform: applies only with a targetSdk; `screen/stage.py` passes none, so `grouping/screen.json` never says `platform_deprecated`.
- future: rows from the SP 800-131A r3 draft are recorded beside the key and never change a verdict.

## Data (`src/perfrepair/catalog/screening.yaml`)

| Section | Key | Holds |
|---|---|---|
| `sources` | short name | the URL a row cites |
| `crypto` | engine type, canonical name | `status` (`deprecated` or `accepted`), `reason`, `source` |
| `components` | engine type, then `base` or `mode` | a `deprecated` rule with `reason` and `source` |
| `platform` | provider, then engine type and canonical names | `deprecatedApi`, `removedApi` (null while still registered), `gate: targetSdk`, `reason`, `source` |
| `future` | engine type, canonical name | `note`, `source` |

## Loader checks (`ScreeningError`, every problem at once)

| Code | When |
|---|---|
| `screening_schema` | `schemaVersion` is not 1 |
| `screening_key_not_canonical` | a key is not the canonical spelling in `algorithm-names.yaml`, carries a key size, or a mode is not a catalog mode |
| `screening_status` | a status outside `deprecated`, `accepted` |
| `screening_source` | a source key absent from `sources`; `unsourced` is allowed |
| `screening_component_status` | a component rule that does not deprecate |
| `screening_gate`, `screening_platform` | an unknown gate; no provider; `removedApi` not after `deprecatedApi` |
| `screening_duplicate` | one (provider, type, name) in two platform rules |
| `screening_contradiction` | an `accepted` crypto row a component rule deprecates |

## Sources policy

- a row cites a fetched source from `sources`, or says `source: unsourced`.
- conflicts follow NIST SP 800-131A r2 (final), stricter where Android's pages say so: SHA-1 digest `deprecated`; PKCS#1 v1.5 signatures `accepted`; CBC `accepted`.
- platform rows come from AOSP `Providers.java` `DEPRECATED_ALGORITHMS`; OIDs and aliases resolve to the canonical names listed; `AlgorithmParameters` and `CertificateFactory` are not item engine types.

## Limits

The key cannot express:

| Fact | Effect |
|---|---|
| key size, curve, group size | `RSA` with a 1024-bit key and with a 4096-bit key get one verdict |
| sign vs verify | a SHA-1 signature is `broken` for verification too |
| collision vs non-collision use | a SHA-1 digest is `broken` for any purpose |
| KDF iterations and salt | password-based AES ciphers and PBKDF2 names stay `unknown`; a PBE name is judged by its cipher alone |
| OAEP and MGF1 digests | a listed OAEP padding is `accepted` whatever MGF1 digest the provider uses |
| bare-name defaults | `AES` and `RSA` are judged by documented defaults, not by what the provider chose |
