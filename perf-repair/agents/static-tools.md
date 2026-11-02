# Static tools

## Calls
- `docs/modes.md` : what each mode counts as an improvement

## Rules
- ratios: `to ÷ from`; below 1 is better; only rows with the same operation, key size, input size and phase pair.
- modes: a mode differs only in its `criteria.yaml` entry; a new criterion is a field on `Mode` set from data, never a name check.
- confidence: pImprove grades, never gates; missing data is `not_measured`, never `no_improvement`.
- triage: every group decidable from numbers alone gets a `static` verdict.
- screening: every consumer asks `screen/handler.py`; a screening status comes from `catalog/screening.yaml` data, never a name in code.

## File structure

```
src/perfrepair/result/confidence.py : pImprove → ok, warn, weak or too_few_runs from criteria.yaml
src/perfrepair/result/criteria.yaml : data: minimum effect ratio, confidence levels, modes
src/perfrepair/result/dossier.py : scopes + app.json + groups + measurements → Dossiers with options, pins, interop status, estimates; failed pairs dropped; noOptions with reasons
src/perfrepair/result/estimate.py : pImprove of one Summary against another by the process- and block-aware bootstrap
src/perfrepair/result/evidence.py : groups.json + rows + measurements → GroupEvidence: configurations, members, ordered pair metrics with pImprove
src/perfrepair/result/modes.py : Mode loaded from criteria.yaml: judges a pair improves, not_improving or not_measured
src/perfrepair/result/triage.py : not_comparable, not_measured and no_improvement verdicts; every group with an improving pair asked
src/perfrepair/screen/__init__.py : the screening package
src/perfrepair/screen/handler.py : ScreeningHandler: (engine type, name, provider, targetSdk) → Verdict by canonical name; crypto and component broken, then gated platform, then accepted, else unknown
src/perfrepair/screen/stage.py : grouping items → a Verdict per item id, no targetSdk
```
