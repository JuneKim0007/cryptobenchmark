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
- A guide rerun of an app that stopped asks nothing already decided: its replace outbox resumes; a done app runs no step ([replacement.md](replacement.md)).
- A prompt or schema edit changes its role's charter fingerprint: the next run asks every pending item once more into a new outbox.
- A record holds `gateway`, `model`, `effort` (schema 2; schema 1 records read back without them). A resume with items left to ask, whose values differ from an earlier record's, logs one line: `mixed_agents: outbox <fingerprint> holds answers from <gateway>/<model>/<effort>, now asking <gateway>/<model>/<effort>`; the answers stay in one outbox.
- A kind's `items()` is every item a record may name (projection, replay, errors); `pending()` is the subset the engine asks, `items()` for every kind but grouping, which leaves out screened-out items. Grouping alone has `gone(key)`: a record's item that left since replays through its stand-in; for the other kinds an unknown item is an error.
- The charter fingerprint hashes the system prompt, schema, correction template and the kind's run inputs; grouping's are empty, or the `refresh <token>` of `assign --refresh`, classify's the whole batched evidence, site-replace's are empty or the `refresh <token>` of `ai replace --refresh`, the other kinds have none and keep their fingerprints.
- Grouping is the other decision kind: `docs/grouping.md`.

## Worthiness

| field | worthiness |
|---|---|
| item | one group of `grouping/groups.json` with an improving pair, not settled by triage |
| message | mode, run warnings, members `M1..Mn`, per configuration (one per benchmark variant, named on its line; never paired across) with pairs and per selected and measured metric (`dto/metrics.py`, [modes.md](modes.md) perfMode; energy with its kind; time in the manifest's display units, with a throughput median column when `throughput` is selected and the configuration has an input size): medians with their 95% bootstrap interval, IQR, cv, n, pair ratios, pImprove with its level (`docs/modes.md`) |
| timings shown | yes |
| answer | `decision` test\|skip, `pairs` [{from, to, reason}], `reason` naming the deciding metrics; code adds each pair's best `pImprove` and `level` |
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
| item | one unit of `<app>/dossiers.json` `units`: its `Link`s, the `Dossier` of each member with options (at least one), the members that stay (`stays`: current and reason) and the inverse pairs' interop (`pairs`); a unit of one is the common case |
| message | the run warnings (`measurements.json` comparability, as worthiness sees them; in the evidence digest when there are any), the unit's members `S1..Sn` and links with their lines, under each inverse link the interop of the items a replace would leave its sides on, per choice, the commonest status once as `every other choice`; the members that stay, with current and reason; then per member with options (a function already shown is `as S1`): site, sinks and key source, the risks code derives from them, one `pattern:` line (the category, its reason and rule, and the `perCall` of the variant shown), the lifecycle (status and reasons, binding, operations, each step's line, `one method away` outside the function) and its requirements (name, origin, line, the taking step's line, origins one method away), current item and name, options `R1..Rn` with pins, interop status (and the risk it adds when not `pass`) and estimates of the selected metrics only (ratio, pImprove, n, per `<metric>@<input size>`, at the nearest input size or, when the site's is unknown, every measured one and said so, the operation, key and phase only where they differ; only the lifecycle's operations when it knows them), then MEASURED: the `primitives.tsv` lines of the current item and each option at the scope's key size and operations, the selected metrics' columns with a value, time as latency and, when selected, throughput in the manifest's display units, n and cv per metric (estimates only when the device folder has no `primitives.tsv`, logged), edit kinds, function source between digest markers |
| answer | `decision` replace\|keep\|recommend for every member with options, `members` [{member, option, edits [{kind, provider, algorithm, parameters [{name, value}]}], risks, needs}] (one per member with options for replace and recommend, [] for keep), `deciding` and `accepted` (metric names), `concerns` (at most 5 short strings, stored, logged per scope as `concerns: …` and carried by the review sheet and report rows; never gated on content), `reason` naming the deciding metrics |
| ids minted by | code: member aliases in unit order; dossier: option aliases per member; the gate resolves them to item ids and the option's typed pins |
| no option | static `keep`, source `static`, never asked; a `no_real_use` lifecycle is one, reason `no_real_use`; an option without an estimate of a metric a listed perfMode selects is dropped, and a scope left none is `no_evidence: <metric>`; such a member stays on what it uses while the unit's others are asked; a unit with a member whose item's key contract is `provider_held` is never asked, its members with options under `provider_held_key` |
| dropped item | every member with options `keep` with reason `dropped: …`, source `fallback` |
| state | `<app>/replacements.json`: `{schemaVersion: 4, app, replacements, sources, stale}`; version 2 moved `set_algorithm` from `parameters.algorithm` to `algorithm`, version 3 added `stale`, version 4 `recommend` with `needs` and `deciding`, `accepted`, `concerns` on every row; a recommend is never edited; the edit step refuses another version; outbox under `<app>/replace/` |
| evidence | each record, keyed by unit id, carries `evidence`, the sha256 of its unit's entry (links, stays, pairs) and every member's dossier JSON (scope facts, source, current, options with pins, interop and estimates), the dossiers' `perfMode` and the stored numbers of the `primitives.tsv` lines shown (never the display units, so a unit change marks nothing stale); every member with options of a unit whose latest record's digest differs from today's, or has none, is `stale`: kept, never re-asked silently, listed in `stale`, and `ai replace` exits with `dossier_changed` naming the scopes (the guide stops there) |
| `--refresh` | the stale units are asked again into a new outbox (inputs `refresh <token>`) that carries every other record; the old outbox stays; later runs read the token from the active charter and stay in it; a prompt change carries nothing |
| gone | a record whose unit is not asked any more replays to no row (`gone`), never a KeyError; a unit whose members changed has a new id and is asked; a scope moved to `noOptions` gets its static keep |
| record | `decision.replacements`: one `Replacement` per member with options; `apply` writes one row per member with options |

## Site replace gate

- The members with options are decided together: `replace` gives each exactly once, each a listed alias of its own options and at least one edit, and names no member that stays; `keep` names no members; `reason` is not empty. Per-member problems name the member. `validate` refuses a state where those members differ in decision or some have no row.
- An inverse link whose sides end on two items after the answer: `fail` refuses it; any status but `pass` needs `unverified_interop` on each swapped side (`S1: risks must include unverified_interop: its inverse S2 ends on …`).
- The message's PERFMODE line gives the rule and the thresholds of the code labels (`result/gain.py`, [modes.md](modes.md#labels)); each option shows its `label` and the metrics improved and worse. `validation/suggest/site_performance.py`:
  - listed perfMode (`strict`): every chosen option passes the verdict's rule (a selected metric at or below `improvingRatio`, none at or above its inverse); `accepted` must be [];
  - `generic` (`overall`): every chosen option improves a metric beyond noise; `deciding` is not empty and each named metric improved for every chosen option; every metric worse for a chosen option is in `accepted`. A trade-off is allowed only this way.
- `recommend`: every member with options names an option with a `change` line, `needs` at least one line, and `edits` []; the risks its scope implies are declared; it is never edited, and the report counts it apart (`funnel.recommend`, `labels.recommend`), never as an improvement. An option above `maxChange` is not in the dossier, so at the default `drop-in` no option has a `change` line and recommend cannot be chosen: those candidates are the report's recommendations.
- A pick whose `change` is above `maxChange` is refused, listed or not; an inverse link whose sides end on two items with a swapped side whose output differs is refused whatever its interop says.
- Edit kinds come from `EDIT_KIND_TABLE` (`dto/replacement.py`), each at most once; each row names the one field its kind fills and what of the option fills it.
- `set_provider` names exactly the option's provider; required when it differs from the current provider.
- `set_algorithm` names exactly the option's name; required when it differs from the current name. Applied as the `algorithm` field.
- An edit fills no field its kind does not use.
- `pin_parameters` equals the option's pins; required when the option has pins, refused when it has none.
- Risks come from `persisted_data`, `wire_format`, `key_compatibility`, `unknown_sink`, `unverified_interop`.
- A `replace` declares at least the risks the scope implies (`DERIVED_RISKS`): sink persist → `persisted_data`, network → `wire_format`, unknown → `unknown_sink`; key source keystore, literal or storage → `key_compatibility`, and unknown or parameter too (where the key comes from is not visible here: scoping stays local, a default-provider call may pick a key store's provider at `init`, and the harness uses a synthetic key, so the swap stays allowed and the risk is declared and reported) (the key source is the lifecycle's key origin when it knows one); the chosen option's interop `not_checkable`, `not_planned` or `not_run` → `unverified_interop`.

## Prompt override

- `paths.prompts` (or `--prompts DIR`) points at a folder holding `suggest/site-replace.system.md`: it replaces the packaged prompt for `ai replace`, the guide and `review stability`.
- A changed prompt is a new charter: its fingerprint opens its own outbox under `<app>/replace/outbox/`, so every unit is asked again there; the packaged outbox stays untouched.
- Removing the override resumes the packaged outbox and its records; nothing is asked again (`tests/test_site_replace_rule.py`).
- The packaged prompt rotated with recommend, concerns, the labels and the security floor: decisions made on the earlier prompt stay in their outbox and are not carried.
- It rotated again with the pattern (decide on the given category's numbers): every unit is asked again in a new outbox.

## Static triage (no model call)

| Verdict | When |
|---|---|
| `not_comparable` | no configuration measured two members |
| `not_measured` | no pair improves, and a faster pair lacks data the mode needs |
| `no_improvement` | no pair improves under the mode, on complete data |

- A group with an improving pair always reaches the model, whatever its pImprove.

## Accuracy sheet

`python3 -m perfrepair.review sheet|score <device>`; `python3 -m perfrepair.review stability <device> --sample N --asks K [--agent ...] [--prompts DIR]` asks N units drawn with a fixed seed across the apps K times each on their unchanged message, gated as usual, commits nothing and writes `review/stability.json` (per unit the picks, free text left out, and `stable`).

- Rows are sorted riskiest first: a `recommend` or a replace whose option's code label is `trade_off`, then other replaces, keeps, then the other kinds.

| `review/decisions.tsv` column | Holds |
|---|---|
| `kind`, `app`, `item` | grouping, classify, worthiness (`app` the mode) or replace (`item` the scope) |
| `pattern`, `patternReason` | a replace row's scope category and its rule; empty for the other kinds |
| `model` | the record's model |
| `facts` | JSON of what code knows: an item's family and known signature; a scope's current, sinks, key source, options, the pick's change class and code label |
| `pick`, `reason` | the answer; `(dropped)` with its problems |
| `concerns` | the answer's concerns, `; `-joined |
| `verdict`, `note` | empty until a person fills them: `ok` or `wrong`; kept across rebuilds while `kind`, `app`, `item` and `pick` stay equal |

| `review/score.json` | Counts |
|---|---|
| `groupingPrecision` | `ok` of the judged grouping rows; null while none is judged |
| `pickAccuracy` | `ok` of the other judged rows |
| `stability` | items asked twice or more on one message whose accepted answers all pick the same, free text left out |
| `gateRejections` | rejected turns per 100 calls, per kind and whole |

- Rows come from the active outboxes; stability and rejections from each stage's `journal.jsonl`; a supervisor turn is in neither.
