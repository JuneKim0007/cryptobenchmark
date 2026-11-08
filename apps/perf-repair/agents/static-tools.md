# Static tools

## Calls
- `docs/modes.md` : what each mode counts as an improvement

## Rules
- ratios: `to ÷ from`; below 1 is better; only rows with the same operation, key size, input size and phase pair.
- modes: one verdict rule in `criteria.yaml` for every perfMode; a mode differs only in its selected metrics, never by a name check.
- confidence: pImprove grades, never gates; missing data is `not_measured`, never a loss.
- screening: every consumer asks `screen/handler.py` built from `screen/catalog.py` `screening_catalog`; a screening status comes from `catalog/screening.yaml` data, never a name in code.

## File structure

```
src/perfrepair/probe/identified.py : the one identified test: screened out, or a contract row the trial agrees with; each device alias the catalog names otherwise
src/perfrepair/result/candidates.py : Family: a scope's candidates outside its group, other canonical names of its family, classed; split into offered (up to maxChange) and not offered
src/perfrepair/result/change.py : a scope's current item against one candidate of its family: pair diff, floor, lost properties, nonce origin, availability at minSdk, measured, screening → change class or every reject reason
src/perfrepair/result/configurations.py : the configurations an option is estimated at: measured on both sides nearest the scope (key size, closest input size, its lifecycle operations), the pins they show, per metric an estimate or the reason compare() gives none, setup_drift across a drifted delta session; cross_session; label and parse_label: the stored configuration text and its fields back
src/perfrepair/result/criteria.yaml : data: minimum effect ratio, confidence levels, the one verdict rule
src/perfrepair/result/dossier.py : scopes + app.json + groups + measurements + the app's screen verdicts → Dossiers, each from its scope pattern's variant only (variant_not_measured when its current item has only the other) with its perCall; noOptions with reasons (no_evidence: <metric>); available_providers
src/perfrepair/result/estimate.py : compare(), the one from/to rule of the dossier estimates: orientation, energy_kinds_differ (not comparable), zero_median (no ratio, pImprove kept); pImprove by the process- and block-aware bootstrap; MIN_RUNS, the runs a side needs, also the gate's low_quality floor
src/perfrepair/result/gain.py : the one rule of a metric's change (improved, worse, unchanged; noise), an option's label, the strict rule of a listed perfMode, no_gain: one estimate proven worse beyond noise and none improving; thresholds from criteria.yaml
src/perfrepair/result/modes.py : criteria(): the one cached read of criteria.yaml, worse_ratio (1 / improvingRatio); Mode: the perfMode the guide and report carry
src/perfrepair/result/options.py : Joined: one variant's options for a scope with pins, interop and screen status, estimates (configurations.py) of the perfMode's metrics only, change classes and track; targets that lower the status, failed pairs, options without a required metric or without any estimate dropped, a current item never measured is current_not_measured; cross_session in needsReview; the candidates not offered
src/perfrepair/result/primitives.py : rows + measurements + run-level screen statuses → the primitives table: one line per (type, algorithm, provider, operation, keySize, phase, variant, status), deprecated ones kept; NotScreened, every measured name with no verdict
src/perfrepair/result/provider_path.py : the provider a site is on for one app: named, or by default order with a shipped provider the app inserts at position 1 ahead; the run name of each provider the app ships
src/perfrepair/result/unit_dossiers.py : a dossiers document grouped by unit: units with a member with options asked, the others' members staying, inverse pairs' interop; a provider-held key contract keeps the unit
src/perfrepair/result/upgrades.py : a broken use's upgrade from code's facts: rank by a candidate's own medians at the site, the edits an option requires, needs_person (sinks, reach, links, held key), settled into an Upgrade
src/perfrepair/screen/__init__.py : the screening package
src/perfrepair/screen/catalog.py : screening_catalog: the catalog every screening step judges by, resolved from `device.screening.catalog` or the packaged file (logged); Catalog (path, sha256, identity, handler, mismatch: `screening_catalog_mismatch`); ai_review
src/perfrepair/screen/evidence.py : unknown items with a canonical name → classify Evidence from the trial and probe; fixed-size batches (BATCH)
src/perfrepair/screen/groups.py : identified items, placed without a model: screened-out items in code-made groups by family, status, canonical name, key holder and a generator's keyMaterial, catalog-listed names in their catalog group at their key contract, an unknown generator alone; stable `code_` ids, fixed descriptions
src/perfrepair/screen/handler.py : ScreeningHandler: (engine type, name, provider, targetSdk) → Verdict by canonical name, recording that name and key size; crypto and component broken, then gated platform, then accepted, else unknown; for_app and app_verdicts raise recorded verdicts by an app's targetSdk
src/perfrepair/screen/stage.py : grouping items → a Verdict per item id, no targetSdk
```
