# Screening

## Statuses

| Status | Meaning |
|---|---|
| `broken` | a `crypto` row says `deprecated`, or a `components` rule matches the transformation |
| `platform_deprecated` | a `platform` row for the item's provider applies and the app's targetSdk is at or above its `deprecatedApi` |
| `unverified` | only with `device.screening.aiReview`: the classify model answered `accepted` for an unknown item; a source, never a target, until a person confirms it |
| `accepted` | a `crypto` row says `accepted` and nothing above applies |
| `unknown` | no row applies, or the name is a `name_conflict`; asked by assign; a target only as the same algorithm (with `device.screening.aiReview` the classify role tries to identify it first) |

## Precedence

`broken` > `platform_deprecated` > `accepted` > `unknown`; the first that applies is the verdict. The model review only changes an `unknown` verdict ([Model review](#model-review)); the don't-lower-the-status rule ranks `broken` < `platform_deprecated` < `unverified` = `unknown` < `accepted` (`dto/screen.py` `RANK`): a model's `accepted` is an opinion, not a citation, so a same-algorithm swap between `unverified` and `unknown` is allowed in both directions.

## Lookup

- key: the engine type and the canonical name from `src/perfrepair/catalog/names.py`, probe aliases included; every spelling of a name gets one verdict.
- key size: dropped; `AES_256/GCM/NoPadding` is looked up as `AES/GCM/NoPadding`.
- components: a transformation `base/mode/padding` is `broken` when its base or its mode is listed.
- nominal mode: a mode the names catalog maps another mode onto for a base (`modeSynonyms`) never matches that base; `RSA/ECB/*` is not ECB.
- platform: applies only with a targetSdk; `screen/stage.py` passes none, so `grouping/screen.json` never says `platform_deprecated`.
- future: rows from the SP 800-131A r3 draft are recorded beside the key and never enforced: no status, target or gate reads them.
- recorded key: each verdict in `screen.json` (schema 5) carries the `canonical` name and `keySize` it was looked up by, and `providerHeld` from the item's key contract; `null` for a `name_conflict`. A `broken` or `platform_deprecated` verdict needs a canonical name. `keySize` is recorded provenance: no group key, status or target rule reads it.

## Use

- grouping: `broken` and `platform_deprecated` items are grouped by code on the recorded key and never asked, whatever their signature says; `groups.json` carries each item's status as `screen` ([grouping.md](grouping.md) Code-made groups).
- a run without `screen.json` asks every item, and dossiers and evidence apply no status rule.
- don't lower the status: a `broken`, `platform_deprecated`, `unverified` or `unknown` target (`NEVER_TARGET`; only a cited `accepted` row may be a different algorithm) is allowed only with the current item's canonical name (any key size: the dossier's pins match it) and at no worse a status (`dto/screen.py` `lowers_status`); dossier options ([replacement.md](replacement.md) Contracts) and worthiness evidence pairs (directed: only the pair into the target is left out) follow it.
- per app: the dossier step raises screen.json's verdict by app.json's `targetSdk` with `ScreeningHandler.for_app`, the gate `verdict` uses; evidence is run-level and sees no platform status.
- handler: `grouping build`, `repair dossier`, the guide and `check` judge by the catalog `screen/catalog.py` `screening_catalog` resolves ([Settings](#settings)); the dossier step takes the handler as a parameter, not from a RunContext, since it has no manifest.
- assign: the prompt does not ask the model to mark a group weak; screening decides it. Removing that clause changed the assign charter fingerprint, so a run assigned before it re-assigns once into a new outbox.

## Settings

| Case | Catalog | Log line (stderr) |
|---|---|---|
| no `perfrepair.yaml` | packaged | `device.screening.catalog: packaged catalog (no perfrepair.yaml); aiReview off` |
| `perfrepair.yaml` without `device.screening.catalog` | packaged | `device.screening.catalog: packaged catalog (device.screening.catalog unset in <file>); aiReview on\|off` |
| `device.screening.catalog` names a file | that file, relative to `perfrepair.yaml` | none |
| `device.screening.catalog` names no file | none: the step exits non-zero with `missing_file` | none |

- Catalog identity: `screen.json` records `catalog: {source, sha256}` (`source` is `packaged` or the file's path); `repair dossier`, the guide (at its prerequisites step, before any other step runs) and `check` compare it with the catalog they resolved and refuse a different `sha256` with `screening_catalog_mismatch`, so a run is never judged by two catalogs. Same content under another path passes.
- A named catalog that does not load, or is no path (`invalid`), is never replaced by the packaged one: skipping screening would let a broken algorithm become a target. The row is `OnInvalid.ERROR`.
- The resolution is the `device.screening.catalog` row of `inputs/table.py` ([settings.md](settings.md) Inputs).

## Model review

With `screening.aiReview: true`, `grouping build` asks the classify role (`ai/parse/algorithm_classify/`, settings role `device.screening.classify`) about the items no catalog row decides, after the static screen and before `screen.json` is written. Off (the default), the build makes no model call.

| Rule | Value |
|---|---|
| asked | `unknown` items with a canonical name; a `name_conflict` has no key a verdict could be recorded by; a sourced row is never second-guessed |
| batch | 10 items per decision, in item order (`screen/evidence.py` `BATCH`); the batch key is its ids |
| evidence | engine type, name, canonical, provider, family, trial `instantiates` and error, `className`, attributes; all recorded by code, no tool that runs code |
| answer | per listed id: `deprecated`, `accepted` or `unsure`, and a reason |
| gate | only listed ids, each exactly once, an allowed value, a non-empty reason (`validation/parse/algorithm_classify.py`) |
| outbox | `grouping/classify/outbox/<fingerprint>/`; the charter inputs are the whole evidence, so another unknown set starts a new outbox and a reverted one resumes; a rebuild resumes without new calls |
| dropped batch | every item of it stays `unknown` (answer `unsure`, reason `dropped: ...`) |
| dry run | `--agent dry-run` answers `unsure` for every id, so no verdict changes |

| Answer | Verdict | Effect |
|---|---|---|
| `deprecated` | `broken`, `source: model:<fingerprint>`, applied at once | grouped by code, never a target; a wrong one only removes a candidate |
| `accepted` | `unverified`, `source: model:<fingerprint>` | asked by assign; a source, never a target (except as the same algorithm); a row in `grouping/registry-candidates.yaml` |
| `unsure` | unchanged `unknown` | none |

- `screen.json` then carries `review: {fingerprint}`; its validator refuses a `model:` source without a `review`, or one that is not `model:<review fingerprint>`, so no verdict is sourced by a model run screen.json does not name; `check` validates the classify outbox, `classify/classified.json` and `registry-candidates.yaml` against it and refuses a model-sourced verdict no answer sets.
- Confirming: a person turns a `registry-candidates.yaml` row (`id`, `type`, `name`, `canonical`, `provider`, `reason`, `fingerprint`) into a sourced `crypto` row of the configured `device.screening.catalog`; the next build screens it `accepted` statically and the model no longer sees it.
- Not yet: JDK legacy and disabled algorithm properties as evidence (a probe addition), citations checked by code.

## Data (`src/perfrepair/catalog/screening.yaml`)

| Section | Key | Holds |
|---|---|---|
| `sources` | short name | the URL a row cites |
| `crypto` | engine type, canonical name | `status` (`deprecated` or `accepted`), `reason`, `source` |
| `components` | engine type, then `base` or `mode` | a `deprecated` rule with `reason` and `source` |
| `platform` | provider, then engine type and canonical names | `deprecatedApi` (compared with the app's targetSdk), `removedApi` (null while still registered), `reason`, `source` |
| `future` | engine type, canonical name | `note`, `source` |

## Loader checks (`ScreeningError`, every problem at once)

| Code | When |
|---|---|
| `screening_schema` | `schemaVersion` is not 1 |
| `screening_yaml`, `screening_shape` | the file is not YAML; a section is not the mapping or list it must be (a configured `device.screening.catalog` can be any file) |
| `screening_key_not_canonical` | a key is not the canonical spelling in `algorithm-names.yaml`, carries a key size, or a mode is not a catalog mode |
| `screening_status` | a status outside `deprecated`, `accepted` |
| `screening_source` | a source key absent from `sources`; `unsourced` is allowed |
| `screening_component_status` | a component rule that does not deprecate |
| `screening_platform` | no provider; `removedApi` not after `deprecatedApi` |
| `screening_duplicate` | one (provider, type, name) in two platform rules |
| `screening_contradiction` | an `accepted` crypto row a component rule deprecates |

## Sources policy

- a row cites a fetched source from `sources`, or says `source: unsourced`.
- conflicts follow NIST SP 800-131A r2 (final), stricter where Android's pages say so: SHA-1 digest `deprecated`; PKCS#1 v1.5 signatures `accepted`; CBC `accepted`.
- platform rows come from AOSP `Providers.java` `DEPRECATED_ALGORITHMS`; OIDs and aliases resolve to the canonical names listed; `AlgorithmParameters` and `CertificateFactory` are not item engine types.
- `NONEwithDSA` follows FIPS 186-5 (final), which r2 predates; the digest-named DSA rows follow r2.
- a row needs a `catalog/types.yaml` row for its family engine and a name in `algorithm-names.yaml`.

## Names with no row

| Names | What the fetched sources say |
|---|---|
| `AES/GCM-SIV/NoPadding` | RFC 8452 is IRTF research output; r2 and the r3 draft do not name it; Android lists it as supported only |
| `NONEwithRSA`, `NONEwithECDSA` and P1363 form | no digest in the name; the caller's digest decides |
| Mac `PBEWithHmacSHA*` | PBMAC1 on SunJCE, the PKCS12 KDF on BC: one key for two schemes |
| Mac `HmacPBESHA*`, `PBEWITHHMACSHA` | RFC 7292 App B deprecates password privacy mode and says integrity mode still uses it |
| `HSS/LMS` | SP 800-208: not suitable for general use, generation in hardware only |
| `SHAKE128-256`, `SHAKE256-512` | FIPS 202: approved XOFs, not approved as hash functions |
| `AES/PCBC/*`, `AES/CTS/NoPadding`, `SunTls*` | no fetched source judges them |
| AES CFB and OFB with a padding or a bit count outside `CFB8`, `CFB128`, `OFB128` | no fetched source judges the padding; other bit counts are not catalog modes |

## Limits

The key cannot express:

| Fact | Effect |
|---|---|
| key size, curve, group size | `RSA` with a 1024-bit key and with a 4096-bit key get one verdict |
| sign vs verify | a SHA-1 signature is `broken` for verification too |
| collision vs non-collision use | a SHA-1 digest is `broken` for any purpose |
| KDF iterations and salt | PBES2 ciphers and PBKDF2 names stay `unknown`; any other PBE name is judged by its cipher or its KDF |
| OAEP and MGF1 digests | a listed OAEP padding is `accepted` whatever MGF1 digest the provider uses |
| bare-name defaults | `AES` and `RSA` are judged by documented defaults, not by what the provider chose |
