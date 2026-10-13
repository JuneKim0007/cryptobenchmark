# Repair

| Step | Input | Output |
|---|---|---|
| candidates | `sites.json`, `grouping/groups.json` | `repair/candidates.json` |
| test-set | candidates | a test set for cryptobenchmark: what the app runs and the alternatives |
| choose | candidates, `worthiness-<mode>/verdicts.json` | `repair/choices.json`: replacement or none, with the reason |
| patch | choices, the app tree | `repair/patches.json`, validated by `validation/repair.py` |
| replay | a `benchmark.json` (+ `energy.json`) | before/after per site |

## Limits
- patch rewrites literals on one line; a call built from variables is left for a person.
- replay times the call's primitive at one input size in the benchmark harness, not the app running.
- the default provider of a site is the first by precedence that registers the name; a provider that
  rejects the key at `init` is not skipped, and a Cipher transformation served only through its base
  service is not resolved.
