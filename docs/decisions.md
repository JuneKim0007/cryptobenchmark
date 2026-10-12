# Decisions

Grouping is a multi-turn decision: `docs/grouping.md`.

| | worthiness |
|---|---|
| item | one group of `grouping/groups.json` with an improving pair |
| message | mode, run warnings, members `M1..Mn`, per configuration: medians, IQR, cv, n, allocations, pair ratios |
| timings shown | yes |
| answer | `decision` test\|skip, `pairs` [{from, to, reason}], `reason` |
| ids minted by | code: aliases resolve to primitive ids |
| fallback | `skip` with source `fallback` |
| state | `worthiness-<mode>/verdicts.json` (Verdicts): static triage plus the projection of the outbox |

## worthiness gate

- `test` names at least one pair; `skip` names none; `reason` is not empty.
- A pair names two different members by alias.
- A pair improves under the mode in at least one configuration; improving only inside IQR overlap is recorded as a warning.

## Both

- A refused answer is asked once more with the problems listed in the message; a second refusal applies the fallback.
- Model: `claude-opus-5-5`, effort `medium`, JSON schema output, server-side refusal fallback.
