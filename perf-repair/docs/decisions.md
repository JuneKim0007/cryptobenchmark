# Decisions

## Engine (every decision kind)

| Limit | Default | Flag |
|---|---|---|
| turns per conversation | 3 | `--turns` |
| conversations per item | 2 | `--sessions` |
| items per call | all | `--limit` |

- A rejected answer gets a correction turn (`prompts/shared/rejection.turn.md`) in the same session, listing its problems.
- A refusal ends the session; the next session re-sends the task with no history of the failed one.
- `--prompts DIR` on `grouping assign`, `grouping report --supervisor`, `ai worthiness`: a file at `DIR/<role>/<name>` overrides that prompt; an unknown file or missing DIR exits 2 (`prompt_unknown`, `missing_directory`).
- After the last conversation the item is committed as a `dropped` record with every problem.
- Commands with a model: `grouping assign`, `grouping report --supervisor`, `ai worthiness`.
- Backend, model and effort: the `PERFREPAIR_*` keys of `.env.example`; `--agent`, `--model`, `--effort` override.
- `grouping report` defaults to effort `high`.
- `claude` backend: JSON schema output, server-side refusal fallback.
- Grouping is the other decision kind: `docs/grouping.md`.

## Worthiness

| field | worthiness |
|---|---|
| item | one group of `grouping/groups.json` with an improving pair, not settled by triage |
| message | mode, run warnings, members `M1..Mn`, per configuration with pairs: medians with their 95% bootstrap interval, IQR, cv, n, allocations, pair ratios, pImprove with its level (`docs/modes.md`) |
| timings shown | yes |
| answer | `decision` test\|skip, `pairs` [{from, to, reason}], `reason`; code adds each pair's best `pImprove` and `level` |
| ids minted by | code: aliases resolve to qualified item names `Type\|name\|provider` |
| dropped item | `skip` with source `fallback` |
| state | `worthiness-<mode>/verdicts.json` (Verdicts): static triage plus the projection of the outbox |

## Worthiness gate

- `test` names at least one pair; `skip` names none; `reason` is not empty.
- A pair names two different members by alias.
- A pair improves under the mode in at least one configuration; a pair whose data is missing is refused as lacking measurements.
- Confidence never refuses a pair: a `warn` or `weak` pair is kept with its level and number.

## Static triage (no model call)

| Verdict | When |
|---|---|
| `not_comparable` | no configuration measured two members |
| `not_measured` | no pair improves, and a faster pair lacks data the mode needs |
| `no_improvement` | no pair improves under the mode, on complete data |

- A group with an improving pair always reaches the model, whatever its pImprove.
