# Decisions

## Engine (every decision kind)

| Limit | Default | Flag |
|---|---|---|
| turns per conversation | 3 | `--turns` |
| conversations per item | 2 | `--sessions` |
| items per call | all | `--limit` |

- A rejected answer gets a correction turn (`prompts/shared/rejection.turn.md`) in the same session, listing its problems.
- A refusal ends the session; the next session re-sends the task with no history of the failed one.
- `--prompts DIR` on `grouping assign`, `grouping report --supervisor`, `ai worthiness`, `ai replace`: a file at `DIR/<role>/<name>` overrides that prompt; an unknown file or missing DIR exits 2 (`prompt_unknown`, `missing_directory`).
- After the last conversation the item is committed as a `dropped` record with every problem.
- Commands with a model: `grouping assign`, `grouping report --supervisor`, `ai worthiness`, `ai replace`.
- Backend, model, effort and the `claude` binary per command: `docs/settings.md`; `--agent`, `--model`, `--effort` override.
- `grouping report` defaults to effort `high`; `PERFREPAIR_EFFORT` does not change it.
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

## Site replace

| field | site-replace |
|---|---|
| item | one `Dossier` of `apps/<app>/dossiers.json` with at least one option |
| message | site, sinks and key source, the risks code derives from them, current item and name, options `R1..Rn` with pins, interop status (and the risk it adds when not `pass`) and estimates (ratio, pImprove, n, configuration), edit kinds, function source between digest markers |
| answer | `decision` replace\|keep, `option` alias or "", `edits` [{kind, provider, algorithm, parameters [{name, value}]}], `risks`, `reason` |
| ids minted by | dossier: option aliases; the gate resolves them to item ids and the option's typed pins |
| no option | static `keep`, source `static`, never asked |
| dropped item | `keep` with reason `dropped: …`, source `fallback` |
| state | `apps/<app>/replacements.json`: `{schemaVersion: 2, app, replacements, sources}`; version 2 moved `set_algorithm` from `parameters.algorithm` to `algorithm`, and the edit step refuses another version; outbox under `apps/<app>/replace/` |

## Site replace gate

- `replace` names a listed alias and at least one edit; `keep` names no option and no edits; `reason` is not empty.
- Edit kinds come from `EDIT_KIND_TABLE` (`dto/site.py`), each at most once; each row names the one field its kind fills and what of the option fills it.
- `set_provider` names exactly the option's provider; required when it differs from the current provider.
- `set_algorithm` names exactly the option's name; required when it differs from the current name. Applied as the `algorithm` field.
- An edit fills no field its kind does not use.
- `pin_parameters` equals the option's pins; required when the option has pins, refused when it has none.
- Risks come from `persisted_data`, `wire_format`, `key_compatibility`, `unknown_sink`, `unverified_interop`.
- A `replace` declares at least the risks the scope implies (`DERIVED_RISKS`): sink persist → `persisted_data`, network → `wire_format`, unknown → `unknown_sink`; key source keystore or literal → `key_compatibility`; the chosen option's interop `not_checkable`, `not_planned` or `not_run` → `unverified_interop`.

## Static triage (no model call)

| Verdict | When |
|---|---|
| `not_comparable` | no configuration measured two members |
| `not_measured` | no pair improves, and a faster pair lacks data the mode needs |
| `no_improvement` | no pair improves under the mode, on complete data |

- A group with an improving pair always reaches the model, whatever its pImprove.
