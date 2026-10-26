# Repair

## Calls
- `docs/repair.md` : steps, inputs, outputs, limits

## Rules
- scope: the model's choice is the worthiness verdict's pair; everything here is a static join, rewrite or report.
- patch: only the string literals of one `getInstance` call change, plus an appended provider argument; a non-literal argument is never rewritten.
- order: candidates → test-set → (benchmark run, grouping, worthiness) → choose → patch → replay.

## File structure

```
src/perfrepair/repair/__main__.py : command: candidates | test-set | choose | patch | replay
src/perfrepair/repair/candidates.py : sites.json × groups.json → each site's item and its group's runnable alternatives
src/perfrepair/repair/choose.py : worthiness verdicts × candidates → the replacement per site, or none with the verdict's reason
src/perfrepair/repair/patch.py : one site rewritten to its replacement; unified diff
src/perfrepair/repair/replay.py : before/after for one site from a benchmark run: mean, median, MB/s, µJ/op
src/perfrepair/repair/test_set.py : candidates → cryptobenchmark test set of the items an app runs and their alternatives
```
