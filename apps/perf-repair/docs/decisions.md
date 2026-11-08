# Decisions

## Engine (every decision kind)

| Limit | Default | Flag |
|---|---|---|
| turns per conversation | 3 | `--turns` |
| conversations per item | 2 | `--sessions` |
| items per call | all | `--limit` |

- A rejected answer gets a correction turn (`prompts/shared/rejection.turn.md`) in the same session, listing its problems.
- A refusal ends the session; the next session re-sends the task with no history of the failed one.
- Budget: `ask` measures the system prompt plus the task message by chars/4 against the role's `budget` ([settings.md](settings.md)) before any call, for every role. Over it, `grouping assign` hides each group a known fact of the item contradicts, a join gate C refuses; a `not known` or assumed component hides nothing. Still over, or any other role over: `over_budget`, naming the role's key and the size, with nothing asked or recorded for the item; no message is ever cut. The schema is left out: it is fixed per role.
- Each turn's size is `promptTokens` in its attempt's entry of `log/ai/<job>.yaml`, with `narrowedFrom` when the prefilter ran.
- `--prompts DIR` on `grouping build` (with `device.screening.aiReview`; off, build refuses it and `--agent`, `--auth`, `--model`, `--effort` since it calls no model), `grouping assign`, `ai replace` and the guide: a file at `DIR/<role>/<name>` overrides that prompt; an unknown file or missing DIR exits 2 (`prompt_unknown`, `missing_directory`).
- After the last conversation the item is committed as a `dropped` record with every problem.
- A provider failure (`AgentFailed`: `claude_cli_failed`, `claude_api_failed`) is no answer: it stops the command with nothing recorded for the item, so a subscription limit never drops one and the next run asks it again. A CLI reply with no output tokens, a non-zero exit with JSON on stdout included, is such a failure.
- Commands with a model: `grouping build` with `device.screening.aiReview`, `grouping assign`, `ai replace`, and the guide through its grouping, upgrade and replace steps.
- Gateway, auth, model and effort per command: `docs/settings.md`; `--agent`, `--auth`, `--model`, `--effort` override.
- `grouping assign` defaults to effort `low`, below every gateway-wide layer; the other roles to `medium`.
- `claude` gateway with `auth: api`: JSON schema output, server-side refusal fallback; the schema is sent without `maxLength`, `minLength` and `pattern`, which the Messages API refuses (400) or may find too complex; the gate still checks them. `auth: subscription` sends the whole schema.
- Answer limits (lengths, id and alias patterns, enums) are each gate's constants, read by its `schema.py` and prompt values; they are part of the answer contract and the charter fingerprint, not settings.
- A guide rerun of an app that stopped asks nothing already decided: its replace outbox resumes; a done app runs no step ([replacement.md](replacement.md)).
- A prompt or schema edit changes its role's charter fingerprint: the next run asks every pending item once more into a new outbox.
- A record holds the `tier` asked (gateway, model, effort, webSearch) and `answered`, the model the provider named (`schemaVersion` 3; another version is refused). The tier is not in the charter fingerprint: another model or effort keeps the outbox and asks only the items still pending, and escalation's records of several tiers sit in one outbox.
- A kind's `items()` is every item a record may name (projection, replay, errors); `pending()` is the subset the engine asks, `items()` for every kind but grouping, which leaves out screened-out and catalog-listed items (`probe/identified.py`), and with `used.json` the items outside it. Grouping alone has `gone(key)`: a record's item that left since replays through its stand-in; for the other kinds an unknown item is an error.
- The charter fingerprint hashes the system prompt, schema, correction template and the kind's run inputs; grouping's are empty, classify's the whole batched evidence, Select's none (its items carry their evidence), the other kinds have none and keep their fingerprints.
- Grouping is the other decision kind: `docs/grouping.md`.

## AI base

| piece | file | does |
|---|---|---|
| `Tier`, `Ladder` | `ai/model/tier.py` | one model choice; a gateway's models (`claude-haiku-5-5`, `claude-sonnet-5-5`, `claude-opus-5-5`), the order escalation climbs; efforts are never climbed |
| `Tool`, `Registry` | `ai/tools/tool.py`, `ai/tools/registry.py` | a job's tools: the model is sent their definitions and may call only them; every call is kept in the attempt's entry |
| read tools | `ai/tools/catalogue_read.py` | `view_for`, `what_is`, `list_groups`, `get_group` |
| schema walk | `validation/schema_walk.py` | the answer's schema is its one source of shape |
| `Repass`, `next_tier` | `ai/attempt/repass.py`, `ai/attempt/escalate.py` | at most 2 repasses with a structured reason, then one step to the next model at the same effort (`MAX_ESCALATIONS` 1) with its own 2 repasses, then `dropped`, a person's: at most 6 attempts per item, and the same cap on a reviewer's own attempts |
| `AttemptLog` | `ai/log/attempt_log.py` | `log/ai/<job>.yaml` |
| `Job` | `ai/job.py` | candidates → render → turns → submit checks → review → repass → escalate → commit → log |

- One turn's answer is one tool call, `{"tool": <name>, "args": {...}}`, under the job's reply schema; transports need no native tool support. A read tool's text comes back as the next turn; a submit runs the job's checks and its problems come back as a correction.
- `Limits.calls` (8) read calls per session before the model must submit; `--turns` counts corrections, `--sessions` fresh conversations.
- `webSearch` on a tier lets the CLI use its WebSearch tool and the API its server web search; nothing else of the CLI's tools is on.
- `<role>.spendCap`: the real tokens one command may use: one count on the role's budget, shared by every job, reviewer and tier the command spawns, of every token the transport reports (input, output, cacheRead, cacheWrite), with the cost where reported; past it, after the attempt is logged, `over_budget`. A failure past the cap raises the failure, not the cap.
- `log/ai/<job>.yaml` (schema 1): `job`, `attempts`, the last key, a block sequence each attempt appends one item to, no earlier line rewritten (a log written whole by an earlier version is put in that form once, when it is opened); per entry `n`, `run`, `app`, `item`, `label`, `attempt`, `tier`, `answered`, `outcome` (`decided`, `refused`, `failed`, `interrupted`, `dropped`), `durationMs`, `tokens`, `costUsd`, `turns` (session, turn, status, problems, text, promptTokens), `calls`, `submitted`, `reason`, `review`, `error`. A provider failure (`failed`) or an interrupt (`interrupted`) is logged with its `error` and the turns made before it, then stops the command.

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

## Select

One job, settings row `apps.replace`, prompt `select`, log `log/ai/select.yaml`; `ai replace` and the guide's upgrade and replace steps run it.

| field | units | broken uses |
|---|---|---|
| item | one unit of `<app>/dossiers.json` `units` | one unlisted `upgrades` row |
| candidates (code) | `ai/select/unit_candidates.py`: each item every member with options offers, with known pins, within `maxChange`, passing the perfMode's rule (`strict`: a selected metric improves and none worsens; `overall`: one improves beyond noise), never ending an inverse partner that stays on a failed pair or another output; `recommend` when another output leaves the function (`OUTPUT_LEAVES`), with what must follow | the ranked secure options |
| answer | `submit(option, reason)`: a candidate's alias, or `none` (keep) | an alias; `none` is not allowed |
| code writes | per member: `edits` (`edits_of`), the risks scope and option imply (and `unverified_interop` for an unchecked inverse partner), `deciding` (improved metrics), `accepted` (worse ones, `overall` only), a recommend's `needs` | `settled`: edit or a person's from the facts ([upgrade.md](upgrade.md)) |
| never asked | `noOptions` scopes: static keeps | listed and unreachable broken uses |
| dropped | every member a `keep`, source `fallback`, reason `dropped: ...` | `needs_migration`, `model_dropped` |
| state | `<app>/replacements.json` (schema 6: app, replacements, sources; each row scope, decision, option, edits, risks, reason, deciding, accepted, needs), outbox `<app>/replace/` | `<app>/upgrades.json`, outbox `<app>/upgrade/` |

- Each record carries its item's evidence digest (the unit entry, the dossiers, the perfMode, the `primitives.tsv` numbers shown and the run warnings); an item whose digest changed is asked again and the old record stays as history. There is no stale state and no `--refresh` for it.
- A unit with no applicable candidate is still asked, `none` its only answer, so the log shows why it was kept.
- Review (`apps.review`, default `false`; the guide built without settings and the tests' direct calls ask none): after a submit passes Select's checks, and only for a pick that will edit code (a unit's `replace` with edits, a broken use's `upgraded`; never `none`, a keep, a `recommend` or a `needs_migration`), `ReviewJob` one tier up the gateway's ladder (the same tier at the top) reads the answer and the message through `read_output` and `read_evidence` and submits `verdict`: `accept` commits; `refuse` with a reason is the next repass's reason; `unidentified` commits the item as a person's (a `fallback` keep, or `needs_migration` with `review_unidentified`), the record naming the reviewer's tier and model as `tier` and `answered`. A reviewer that never settles is `unidentified`. Its attempts are `log/ai/review.yaml`.
- `paths.prompts` (or `--prompts DIR`) holding `select.system.md` replaces the packaged prompt: a new charter, a new outbox; removing it resumes the packaged one.

## Accuracy sheet

`python3 -m perfrepair.review sheet|score <device>`.

- Rows are sorted riskiest first: a `recommend` or a replace whose option's code label is `trade_off`, then other replaces, keeps, then the other kinds.

| `review/decisions.tsv` column | Holds |
|---|---|
| `kind`, `app`, `item` | grouping, classify or replace (`item` the scope) |
| `pattern`, `patternReason` | a replace row's scope category and its rule; empty for the other kinds |
| `model` | the record's model |
| `facts` | JSON of what code knows: an item's family and known signature; a scope's current, sinks, key source, options, the pick's change class and code label |
| `pick`, `reason` | the answer; `(dropped)` with its problems |
| `verdict`, `note` | empty until a person fills them: `ok` or `wrong`; kept across rebuilds while `kind`, `app`, `item` and `pick` stay equal |

| `review/score.json` | Counts |
|---|---|
| `groupingPrecision` | `ok` of the judged grouping rows; null while none is judged |
| `pickAccuracy` | `ok` of the other judged rows |
| `gateRejections` | rejected turns per 100 calls, per kind and whole |

- Rows come from the active outboxes; rejections from each job's `log/ai/<job>.yaml`.
