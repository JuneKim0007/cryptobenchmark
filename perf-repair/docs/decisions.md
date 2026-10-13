# Decisions

Grouping is a multi-turn decision: `docs/grouping.md`.

| | worthiness |
|---|---|
| item | one group of `grouping/groups.json` with an improving pair |
| message | mode, run warnings, members `M1..Mn`, per configuration: medians with their 95% interval, IQR, cv, n, allocations, pair ratios |
| timings shown | yes |
| answer | `decision` test\|skip, `pairs` [{from, to, reason}], `reason` |
| ids minted by | code: aliases resolve to primitive ids |
| fallback | `skip` with source `fallback` |
| state | `worthiness-<mode>/verdicts.json` (Verdicts): static triage plus the projection of the outbox |

## worthiness gate

- `test` names at least one pair; `skip` names none; `reason` is not empty.
- A pair names two different members by alias.
- A pair improves under the mode in at least one configuration; improving only where the medians' 95% intervals overlap is settled statically as `within_noise`.

## Both

- A refused answer is asked once more with the problems listed in the message; a second refusal applies the fallback.
- Model: `claude-opus-5-5`, effort `medium`, JSON schema output, server-side refusal fallback.

## Static triage (no model call)

| Verdict | When |
|---|---|
| `not_comparable` | no configuration measured two members |
| `no_improvement` | no pair improves under the mode |
| `within_noise` | every improving pair's median 95% intervals overlap (order statistics, distribution-free); a 20% CoV with a clear gap is still evidence |
