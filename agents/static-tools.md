# Static tools

## Calls
- `docs/modes.md` : what each mode counts as an improvement

## Rules
- scope: a static tool computes; it never asks a model.
- ratios: `to ÷ from`; below 1 is better; only rows with the same operation, key size, input size and phase pair.
- modes: a mode changes only `Mode.improves`; a new criterion is a new mode, not a flag.
- triage: every group decidable from numbers alone gets a `static` verdict.

## File structure

```
src/perfrepair/result/evidence.py : groups.json + rows + measurements → GroupEvidence: configurations, members, ordered pair metrics
src/perfrepair/result/modes.py : latency and battery (proxy) improvement criteria
src/perfrepair/result/triage.py : not_comparable and no_improvement verdicts; the rest asked
```
