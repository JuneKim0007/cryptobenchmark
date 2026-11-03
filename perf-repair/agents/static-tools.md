# Static tools

## Calls
- `docs/modes.md` : what each mode counts as an improvement

## Rules
- ratios: `to ÷ from`; below 1 is better; only rows with the same operation, key size, input size and phase pair.
- modes: a mode differs only in its `criteria.yaml` entry; a new criterion is a field on `Mode` set from data, never a name check.
- confidence: pImprove grades, never gates; missing data is `not_measured`, never `no_improvement`.
- triage: every group decidable from numbers alone gets a `static` verdict.
- screening: every consumer asks `screen/handler.py` built from `screen/catalog.py` `screening_catalog`; a screening status comes from `catalog/screening.yaml` data, never a name in code.

## File structure

```
src/perfrepair/result/confidence.py : pImprove → ok, warn, weak or too_few_runs from criteria.yaml
src/perfrepair/result/criteria.yaml : data: minimum effect ratio, confidence levels, modes
src/perfrepair/result/dossier.py : scopes + app.json + groups + measurements + the app's screen verdicts → Dossiers with options, pins, interop and screen status, estimates; targets that lower the status and failed pairs dropped; noOptions with reasons
src/perfrepair/result/estimate.py : pImprove of one Summary against another by the process- and block-aware bootstrap
src/perfrepair/result/evidence.py : groups.json + rows + measurements + run-level screen verdicts → GroupEvidence: configurations, members, ordered pair metrics with a ratio and pImprove per registry metric (never across energy kinds); a pair whose target lowers the status left out
src/perfrepair/result/modes.py : Mode loaded from criteria.yaml: judges a pair improves, not_improving or not_measured
src/perfrepair/result/primitives.py : rows + measurements + run-level screen statuses → the primitives table: one line per (type, algorithm, provider, operation, keySize, phase, status), deprecated ones kept
src/perfrepair/result/triage.py : not_comparable, not_measured and no_improvement verdicts; every group with an improving pair asked
src/perfrepair/result/unit_dossiers.py : a dossiers document grouped by unit: units with a member with options asked, the others' members staying, inverse pairs' interop; a provider-held key contract keeps the unit
src/perfrepair/screen/__init__.py : the screening package
src/perfrepair/screen/catalog.py : screening_catalog: the catalog every screening step judges by, resolved from `device.screening.catalog` or the packaged file (logged); Catalog (path, sha256, identity, handler, mismatch: `screening_catalog_mismatch`); ai_review
src/perfrepair/screen/evidence.py : unknown items with a canonical name → classify Evidence from the trial and probe; fixed-size batches (BATCH)
src/perfrepair/screen/groups.py : code-made groups: screened-out items grouped by family, status and canonical name, items with a decided signature by family and signature; stable `code_` ids, fixed description
src/perfrepair/screen/handler.py : ScreeningHandler: (engine type, name, provider, targetSdk) → Verdict by canonical name, recording that name and key size; crypto and component broken, then gated platform, then accepted, else unknown; for_app and app_verdicts raise recorded verdicts by an app's targetSdk
src/perfrepair/screen/stage.py : grouping items → a Verdict per item id, no targetSdk
```
