# Decisions

## Engine (every decision kind)

| Limit | Default | Flag |
|---|---|---|
| turns per conversation | 3 | `--turns` |
| conversations per item | 2 | `--sessions` |
| items per call | all | `--limit` |

- A rejected answer gets a correction turn (`prompts/shared/rejection.turn.md`) in the same session, listing its problems.
- A refusal ends the session; the next session re-sends the task with no history of the failed one.
- `--prompts DIR` on `grouping build` (with `device.screening.aiReview`; off, build refuses it and `--agent`, `--auth`, `--model`, `--effort` since it calls no model), `grouping assign`, `grouping report --supervisor`, `ai worthiness`, `ai replace`: a file at `DIR/<role>/<name>` overrides that prompt; an unknown file or missing DIR exits 2 (`prompt_unknown`, `missing_directory`).
- After the last conversation the item is committed as a `dropped` record with every problem.
- A provider failure (`AgentFailed`: `claude_cli_failed`, `claude_api_failed`) is no answer: it stops the command with nothing recorded for the item, so a subscription limit never drops one and the next run asks it again. A CLI reply with no output tokens, a non-zero exit with JSON on stdout included, is such a failure.
- Commands with a model: `grouping build` with `device.screening.aiReview`, `grouping assign`, `grouping report --supervisor`, `ai worthiness`, `ai replace`.
- Gateway, auth, model and effort per command: `docs/settings.md`; `--agent`, `--auth`, `--model`, `--effort` override.
- `grouping assign` defaults to effort `low`, below every gateway-wide layer; the other roles to `medium`.
- `claude` gateway with `auth: api`: JSON schema output, server-side refusal fallback; the schema is sent without `maxLength`, `minLength` and `pattern`, which the Messages API refuses (400) or may find too complex; the gate still checks them. `auth: subscription` sends the whole schema.
- Answer limits (lengths, id and alias patterns, enums) are each gate's constants, read by its `schema.py` and prompt values; they are part of the answer contract and the charter fingerprint, not settings.
- A prompt or schema edit changes its role's charter fingerprint: the next run asks every pending item once more into a new outbox.
- A record holds `gateway`, `model`, `effort` (schema 2; schema 1 records read back without them). A resume with items left to ask, whose values differ from an earlier record's, logs one line: `mixed_agents: outbox <fingerprint> holds answers from <gateway>/<model>/<effort>, now asking <gateway>/<model>/<effort>`; the answers stay in one outbox.
- A kind's `items()` is every item a record may name (projection, replay, errors); `pending()` is the subset the engine asks, `items()` for every kind but grouping, which leaves out screened-out items. Grouping alone has `gone(key)`: a record's item that left since replays through its stand-in; for the other kinds an unknown item is an error.
- The charter fingerprint hashes the system prompt, schema, correction template and the kind's run inputs; grouping's are empty, or the `refresh <token>` of `assign --refresh`, classify's the whole batched evidence, site-replace's are empty or the `refresh <token>` of `ai replace --refresh`, the other kinds have none and keep their fingerprints.
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

## Algorithm classify

| field | algorithm-classify |
|---|---|
| item | one batch of up to 10 `unknown` items with a canonical name ([screening.md](screening.md) Model review) |
| message | per id: engine type, name, canonical, provider, family, trial (instantiates, error), className, attributes |
| timings shown | no |
| answer | `answers` [{id, answer deprecated\|accepted\|unsure, reason}] |
| ids minted by | code: item ids; the batch key is the ids joined by `,` |
| dropped item | every id `unsure` with reason `dropped: ...`: the items stay `unknown` |
| state | `grouping/classify/classified.json`, merged into `screen.json` by `with_answer`; `registry-candidates.yaml` |

## Site replace

| field | site-replace |
|---|---|
| item | one `Dossier` of `<app>/dossiers.json` with at least one option |
| message | site, sinks and key source, the risks code derives from them, the lifecycle (status and reasons, binding, operations, each step's line, `one method away` outside the function) and its requirements (name, origin, line, the taking step's line, origins one method away), current item and name, options `R1..Rn` with pins, interop status (and the risk it adds when not `pass`) and estimates (ratio, pImprove, n, configuration; only the lifecycle's operations when it knows them), edit kinds, function source between digest markers |
| answer | `decision` replace\|keep, `option` alias or "", `edits` [{kind, provider, algorithm, parameters [{name, value}]}], `risks`, `reason` |
| ids minted by | dossier: option aliases; the gate resolves them to item ids and the option's typed pins |
| no option | static `keep`, source `static`, never asked; a `no_real_use` lifecycle is one, reason `no_real_use` |
| dropped item | `keep` with reason `dropped: …`, source `fallback` |
| state | `<app>/replacements.json`: `{schemaVersion: 3, app, replacements, sources, stale}`; version 2 moved `set_algorithm` from `parameters.algorithm` to `algorithm`, version 3 added `stale`; the edit step refuses another version; outbox under `<app>/replace/` |
| evidence | each record carries `evidence`, the sha256 of its dossier's JSON (scope facts, source, current, options with pins, interop and estimates); a scope whose latest record's digest differs from today's dossier, or has none, is `stale`: kept, never re-asked silently, listed in `stale`, and `ai replace` exits with `dossier_changed` naming the scopes (the guide stops there) |
| `--refresh` | the stale scopes are asked again into a new outbox (inputs `refresh <token>`) that carries every other record; the old outbox stays; later runs read the token from the active charter and stay in it; a prompt change carries nothing |
| gone | a record whose scope has no dossier any more replays to no row (`gone`), never a KeyError; a scope moved to `noOptions` gets its static keep |

## Site replace gate

- `replace` names a listed alias and at least one edit; `keep` names no option and no edits; `reason` is not empty.
- Edit kinds come from `EDIT_KIND_TABLE` (`dto/site.py`), each at most once; each row names the one field its kind fills and what of the option fills it.
- `set_provider` names exactly the option's provider; required when it differs from the current provider.
- `set_algorithm` names exactly the option's name; required when it differs from the current name. Applied as the `algorithm` field.
- An edit fills no field its kind does not use.
- `pin_parameters` equals the option's pins; required when the option has pins, refused when it has none.
- Risks come from `persisted_data`, `wire_format`, `key_compatibility`, `unknown_sink`, `unverified_interop`.
- A `replace` declares at least the risks the scope implies (`DERIVED_RISKS`): sink persist → `persisted_data`, network → `wire_format`, unknown → `unknown_sink`; key source keystore or literal → `key_compatibility` (the key source is the lifecycle's key origin when it knows one); the chosen option's interop `not_checkable`, `not_planned` or `not_run` → `unverified_interop`.

## Static triage (no model call)

| Verdict | When |
|---|---|
| `not_comparable` | no configuration measured two members |
| `not_measured` | no pair improves, and a faster pair lacks data the mode needs |
| `no_improvement` | no pair improves under the mode, on complete data |

- A group with an improving pair always reaches the model, whatever its pImprove.
