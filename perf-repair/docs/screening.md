# Screening

## Statuses

| Status | Meaning |
|---|---|
| `broken` | a `crypto` row says `deprecated`, or a `components` rule matches the transformation |
| `platform_deprecated` | a `platform` row for the item's provider applies and the app's targetSdk is at or above its `deprecatedApi` |
| `unverified` | only with `screening.aiReview`: the classify model answered `accepted` for an unknown item; a source, never a target, until a person confirms it |
| `accepted` | a `crypto` row says `accepted` and nothing above applies |
| `unknown` | no row applies, or the name is a `name_conflict` |

## Precedence

`broken` > `platform_deprecated` > `accepted` > `unknown`; the first that applies is the verdict. The model review only changes an `unknown` verdict ([Model review](#model-review)); `STATUSES` orders `unverified` between `platform_deprecated` and `accepted` for the don't-lower-the-status rule.

## Lookup

- key: the engine type and the canonical name from `src/perfrepair/catalog/names.py`, probe aliases included; every spelling of a name gets one verdict.
- key size: dropped; `AES_256/GCM/NoPadding` is looked up as `AES/GCM/NoPadding`.
- components: a transformation `base/mode/padding` is `broken` when its base or its mode is listed.
- nominal mode: a mode the names catalog maps another mode onto for a base (`modeSynonyms`) never matches that base; `RSA/ECB/*` is not ECB.
- platform: applies only with a targetSdk; `screen/stage.py` passes none, so `grouping/screen.json` never says `platform_deprecated`.
- future: rows from the SP 800-131A r3 draft are recorded beside the key and never change a verdict.
- recorded key: each verdict in `screen.json` (schema 3) carries the `canonical` name and `keySize` it was looked up by; `null` for a `name_conflict`. A `broken` or `platform_deprecated` verdict needs one.

## Use

- grouping: `broken` and `platform_deprecated` items are grouped by code on the recorded key and never asked; `groups.json` carries each item's status as `screen` ([grouping.md](grouping.md) Code-made groups).
- a run without `screen.json` asks every item, and dossiers and evidence apply no status rule.
- don't lower the status: a `broken`, `platform_deprecated` or `unverified` target (`NEVER_TARGET`) is allowed only with the current item's canonical name and key size and at no worse a status (`dto/screen.py` `lowers_status`); dossier options ([replacement.md](replacement.md) Contracts) and worthiness evidence pairs (directed: only the pair into the target is left out) follow it.
- per app: the dossier step raises screen.json's verdict by app.json's `targetSdk` with `ScreeningHandler.for_app`, the gate `verdict` uses; evidence is run-level and sees no platform status.
- handler: `grouping build`, `repair dossier`, the guide and `check` judge by the catalog `screen/catalog.py` `screening_catalog` resolves ([Settings](#settings)); the dossier step takes the handler as a parameter, not from a RunContext, since it has no manifest.
- assign: the prompt does not ask the model to mark a group weak; screening decides it. Removing that clause changed the assign charter fingerprint, so a run assigned before it re-assigns once into a new outbox.

## Settings

| Case | Catalog | Log line (stderr) |
|---|---|---|
| no `perfrepair.yaml` | packaged | `screening.catalog: packaged catalog (no perfrepair.yaml); aiReview off` |
| `perfrepair.yaml` without `screening.catalog` | packaged | `screening.catalog: packaged catalog (screening.catalog unset in <file>); aiReview on\|off` |
| `screening.catalog` names a file | that file, relative to `perfrepair.yaml` | none |
| `screening.catalog` names no file | none: the step exits non-zero with `missing_file` | none |

- Catalog identity: `screen.json` records `catalog: {source, sha256}` (`source` is `packaged` or the file's path); `repair dossier`, the guide's dossier step and `check` compare it with the catalog they resolved and refuse a different `sha256` with `screening_catalog_mismatch`, so a run is never judged by two catalogs. Same content under another path passes.
- A named catalog that does not load is never replaced by the packaged one: skipping screening would let a broken algorithm become a target.
- The resolution is the `screening.catalog` row of `inputs/table.py` ([settings.md](settings.md) Inputs).

## Model review

With `screening.aiReview: true`, `grouping build` asks the classify role (`ai/parse/algorithm_classify/`, settings role `screening.classify`) about the items no catalog row decides, after the static screen and before `screen.json` is written. Off (the default), the build makes no model call.

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

- `screen.json` then carries `review: {fingerprint}`; `check` validates the classify outbox, `classify/classified.json` and `registry-candidates.yaml` against it and refuses a model-sourced verdict no answer sets.
- Confirming: a person turns a `registry-candidates.yaml` row (`id`, `type`, `name`, `canonical`, `provider`, `reason`, `fingerprint`) into a sourced `crypto` row of the configured `screening.catalog`; the next build screens it `accepted` statically and the model no longer sees it.
- Not yet: JDK legacy and disabled algorithm properties as evidence (a probe addition), citations checked by code.

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
