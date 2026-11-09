# Decisions

## Calls
- `docs/decisions.md` : the engine's retry and model defaults; what each decision sees, answers, and its gate
- `agents/validation.md` : the validator every decision state needs
- `docs/settings.md` : perfrepair.yaml and .env: lookup, precedence, keys, roles

## Rules
- role: a model call decides one item.
- context: items are context-free: each session starts from the system prompt + the item's TaskPrompt; later turns in a session carry only CorrectionPrompts.
- input: a rendered message carries only what the decision needs; assignment never sees timings.
- budget: `ask` checks every role's message against its `budget` once; over it, a kind's `narrowed` hides only what gate C refuses, then `over_budget`; never a cut message.
- ids: code mints item ids and member aliases (`M1..Mn`) and resolves them; a grouping answer mints a new group id, checked by gate C.
- gate: every answer passes the kind's `check` before `apply`.
- retry: a rejected answer gets a correction turn in the same session (`--turns`); a refusal ends the session; the next session re-sends the task (`--sessions`); then the item is committed as `dropped`.
- spawn: an agent starts one way: the role's kind builds its charter from `PromptLibrary`, `ai/runtime/gateway/spawn` gives the conversations, `ai/runtime/engine` opens one fresh conversation per item with the kind's rendered knowledge; `tests/test_layers.py` refuses any other path.
- log: a stage reports through `log/emit.py` (`step`, `emit`), never its own format.
- unit: a decision over coupled scopes is one item keyed by unit; its members with options are replaced together or kept together, a member without options stays; apply writes one row per member with options.
- select, never aggregate: code reads, joins and stores the data (scopes, benchmark rows, groups, dossiers); a model chooses among the stored options by alias for one item and never reads raw benchmark data or computes a number.
- commit: the outbox record is the only commit; state is `project(kind, records)` and `validate` must check it equals the saved state.
- log: every attempt of every job is one entry of `log/ai/<job>.yaml` (`ai/log/attempt_log.py`), opened at the job's start even when it asks nothing, with its tier, the model that answered, turns, tool calls, submit, reason and review; its event carries only a pointer and counts.
- job: a new AI job is a `Job` subclass (`ai/job.py`): it gives candidates, render, checks, decide and apply; the loop (turns, submit checks, review, repass, escalation, commit, log) is the base's and a subclass that overrides it is refused at import.
- tools: a job's model sees and calls only its own tools (`ai/tools/registry.py`); reads go through `ai/tools/catalogue_read.py`, never a file; its submit tool runs its `checks`.
- shape: an answer's JSON schema is its one source; `validation/schema_walk.py` walks it before the job's checks, no hand validator repeats it.
- repass: an attempt with no accepted submit, or refused by Review, gives a structured reason; at most 2 repasses carry it, then one step to the next model of the gateway's ladder (`ai/attempt/escalate.py`, never another effort) with 2 more, then `dropped`, a person's: 6 attempts at most per item, a reviewer's own included.
- tier: the charter fingerprint hashes every tool definition, never the tier (gateway, model, effort, webSearch): another model asks no decided item again; a record holds the tier asked and the model that answered.
- settings: a key in `perfrepair.yaml` is a row in `inputs/table.py` with exactly one reader, and ships only with the code that reads it; a role default lives in its `RoleRow`, never in a command.
- settings: `OnInvalid.ERROR` only where a fallback is unsafe; a bad flag always errors.
- settings: secrets stay in the environment or `.env`; the child of `auth: subscription` never receives `ANTHROPIC_API_KEY`.
- gateway: provider differences (schema stripping, child environment, CLI flags, effort levels) stay inside its modules under `ai/runtime/gateway/`; the engine and `Conversations` name no provider.
- gateway: a setting ships with the code that reads it; no block or stub for a provider without a gateway.
- gateway: every model command calls `gateway/spawn.py` before its work.
- prompts: read only through `PromptLibrary`; a changed prompt changes the charter fingerprint and starts a new outbox.

## Workflow
- add a job: a `Job` subclass in `ai/<job>/job.py` (name, prompt, submit schema, candidates, render, checks, decide, apply, finish); its code-side inputs one file each beside it; its prompt under `prompts/` and its `prompts.yaml` entry; a scripted-transport test of its checks; map lines → `docs/decisions.md`
- change a prompt: its gate and `docs/decisions.md` in the same change
- add a provider: `ai/runtime/gateway/<name>.py` with a `Gateway` (settings dataclass, secret, spawn) → its row in `registry.py` → map line → `docs/settings.md`

## File structure

```
src/perfrepair/ai/__main__.py : command: `ai replace`, Select over an app's broken uses then its units
src/perfrepair/ai/attempt/escalate.py : next_tier: the next model up the gateway's ladder at the same effort, else none; MAX_ESCALATIONS (1) steps per item
src/perfrepair/ai/attempt/repass.py : Reason (source checks, no_submit or review; problems), Repass: at most MAX_REPASSES (2) fresh attempts carrying the earlier reasons
src/perfrepair/ai/job.py : Job: the template of every AI job: candidates, render, turns, the submit tool's checks, review, repass, escalation, commit, log; sealed against override
src/perfrepair/ai/log/attempt_log.py : AttemptLog: log/ai/<job>.yaml opened at the job's start, one entry appended per attempt, read_log for its readers, each also one pointer event with counts and one TTY line
src/perfrepair/ai/log/where.py : Where: the stage, step and app a job's attempts belong to
src/perfrepair/ai/model/tier.py : Tier (gateway, model, effort, webSearch), the one model choice; Ladder: a gateway's models weakest first
src/perfrepair/ai/review/job.py : ReviewJob: one tier up, reads another job's answer (read_output) and evidence (read_evidence) and the catalogue; verdict accept, refuse (the job's next repass reason) or unidentified (a person's)
src/perfrepair/ai/runtime/agent/conversation.py : Conversation and Conversations: the multi-turn protocol, its lifetime guard, scripted answers
src/perfrepair/ai/runtime/agent/reply.py : AgentReply, AgentRefused, AgentFailed (a provider's one coded failure line)
src/perfrepair/ai/runtime/engine/ask.py : one item's asking: the budget check, turns in a conversation (a read tool's result is a turn too, up to Limits.calls), then fresh conversations; Answer; each turn's model latency and size
src/perfrepair/ai/runtime/engine/budget.py : a role's Budget, the chars/4 measure, the fit: the message, the kind's narrowed one, or `over_budget`
src/perfrepair/ai/runtime/engine/charter_file.py : an outbox's charter.json: written once, checked on each open (`charter_mismatch`), rehashed by the validator; a recorded charter's inputs
src/perfrepair/ai/runtime/engine/decide.py : the item loop of the kinds Identify replaces (classify, grouping): gates, ask, durable commit, projections, --limit; each attempt into log/ai/<kind>.yaml; start and end events
src/perfrepair/ai/runtime/engine/events.py : the real tokens and cost of a job's turns, from their replies' usage
src/perfrepair/ai/runtime/engine/kind.py : DecisionKind contract (items for lookup, pending to ask, documents to write, optional gone, admit, evidence_digest and narrowed), item_of, evidence_of, project(kind, records), replay_problems: version count and replay equality; rebuild_problems: each file byte for byte
src/perfrepair/ai/runtime/engine/outbox.py : the only commit: durable, exclusive, ordered records per charter fingerprint; charter.json before the first record; `active` pointer
src/perfrepair/ai/runtime/gateway/args.py : --agent, --auth, --model, --effort per role, with each role's default and the gateways' choices in the help
src/perfrepair/ai/runtime/gateway/claude.py : the claude gateway: ClaudeSettings (auth, model, effort, binary; its effort levels), the secret auth api needs, spawn by auth, the CLI with timeouts.claude
src/perfrepair/ai/runtime/gateway/claude_api.py : Messages API transport: whole message list per request, cached system prompt, JSON schema output without the keywords the API refuses (`API_UNSUPPORTED`), server-side refusal fallback
src/perfrepair/ai/runtime/gateway/claude_cli.py : Claude CLI headless (`claude -p`) transport: isolated sessions, --resume, existing login, the child's environment from child_env; a work folder it made removed with it; ClaudeCliError `claude_cli_failed`, a CLI that cannot run included; a call past its timeout killed with its children, `claude_cli_timeout`
src/perfrepair/ai/runtime/gateway/contract.py : Gateway: what one provider declares: name, settings class, spawn, secret, choices
src/perfrepair/ai/runtime/gateway/dry_run.py : the dry-run gateway: no keys, answers with the role's stand-in
src/perfrepair/ai/runtime/gateway/registry.py : name → Gateway; the default gateway; `unknown_gateway`
src/perfrepair/ai/runtime/gateway/spawn.py : the one spawn handler: role → gateway → every block checked (each key by the gateway's settings class) and resolved values → secret check → Conversations with their AgentIdentity and the role's Budget; Spawned.at: one client per tier for the command
src/perfrepair/ai/runtime/prompt/args.py : --prompts DIR on every model-calling command; the one reader of `paths.prompts`; one library load per invocation, PromptError exits 2
src/perfrepair/ai/runtime/prompt/library.py : PromptLibrary: reads prompts.yaml and the prompt files once, checks them, fills declared values; each prompt's origin, `packaged` or its override file
src/perfrepair/ai/select/candidate.py : Pick, Candidate (alias, item, replace, recommend or upgrade, picks, needs), SelectItem (key, label, candidates, none allowed, evidence digest, message)
src/perfrepair/ai/select/command.py : select_upgrades, select_units: one SelectJob per source under apps.replace into log/ai/select.yaml; the dry run (none, else the first candidate; a review accepted); upgrade_counts
src/perfrepair/ai/select/job.py : SelectJob: submit(option, reason) checked against the item's answers; code's decision from the candidate; reviewed only when the pick edits code; the source's state and documents
src/perfrepair/ai/select/links.py : the unit's links and each inverse pair's interop per choice a swap leaves, the commonest status once
src/perfrepair/ai/select/options.py : one option's lines: item, pins (or unknown), change, interop and the risk it adds, its code label and needs review, estimates on one line
src/perfrepair/ai/select/render.py : the unit message: run warnings, PERFMODE rule, members and links, the members that stay; per member site, scope facts, lifecycle, current, the options a candidate uses, MEASURED, fenced source; CANDIDATES
src/perfrepair/ai/select/replacements.py : Replacements: one Replacement and its source (llm, fallback, static) per scope
src/perfrepair/ai/select/replay.py : replay_problems: a source's file checked as written, then rebuilt from its outbox byte for byte
src/perfrepair/ai/select/rows.py : the primitives.tsv lines a member is shown, their columns in the display units, and the stored numbers its evidence digest hashes
src/perfrepair/ai/select/unit_candidates.py : a unit's candidates by code: items every member offers, under maxChange, known pins, the perfMode rule, inverse partners kept readable; risks; recommend when another output leaves
src/perfrepair/ai/select/units.py : UnitSource: the units of dossiers.json as items, their evidence digest, the rows code writes for a pick (edits, risks, deciding, accepted), replacements.json
src/perfrepair/ai/select/upgrade_render.py : the broken-use message: site, sinks and reach, the current and screening's reason, the ranked candidates with medians and any ratio
src/perfrepair/ai/select/upgrade_state.py : UpgradeState: one Upgrade per broken use
src/perfrepair/ai/select/upgrades.py : UpgradeSource: listed and unreachable broken uses settled by code, the rest asked with no none; upgrades.json
src/perfrepair/ai/tools/catalogue_read.py : the read tools view_for, what_is, list_groups, get_group over ../../lib/cryptobench/cryptobench/catalogue/views.py and ../../lib/cryptobench/cryptobench/catalogue/glossary.py; JSON text out, a coded error as the problem
src/perfrepair/ai/tools/registry.py : Registry: tools by job, exactly one submit each; surface and reply schema per job; call: out of scope reads as unknown, arguments walked, every call kept on the Context
src/perfrepair/ai/tools/tool.py : Tool (name, description, schema, kind read or submit, run), Outcome, Context of one conversation's calls
src/perfrepair/config/__init__.py : docstring only
src/perfrepair/config/args.py : --perfrepair-config; one settings load per command, which installs the stops reader; unset flags filled from their rows; positive_int, the argparse type of --turns, --sessions, --limit
src/perfrepair/config/current.py : the run's settings: the first command of a run that loads them installs them, an in-process command keeps its caller's; read when a code fires or a child starts
src/perfrepair/config/device_results.py : the device folder of a command: --device-results, else --results-root with device.id or its only device, device.id's one reader; device_root (the root the guide hands to probe_device); not_device_results; the temporary-folder warning
src/perfrepair/config/dotenv.py : .env reader: its PERFREPAIR_* keys as a layer; other keys fill unset environment keys
src/perfrepair/config/load.py : settings file lookup; read a row, or a role's key, by its chain; each value's source, logged once (INFO from a file or the environment, else DEBUG)
src/perfrepair/config/settings.py : reads perfrepair.yaml: secret_key anywhere, unknown_key warnings from the rows' keys, a section's shape; raw values and aiGateway blocks
src/perfrepair/config/stops.py : the one reader of stops.<code> (STOP_ROWS), read when the code fires: unset the default, bad one warning and the default, a fixed code set one stop_fixed warning (once per load); install_stops installs the run's settings and this reader
src/perfrepair/config/timeouts.py : the one reader of timeouts.claude and timeouts.pipeline, from the run's settings when a child starts; the row default without settings
src/perfrepair/prompts/parse/algorithm-classify.system.md : system prompt: deprecated, accepted or unsure per listed id; when in doubt unsure; reason each
src/perfrepair/prompts/parse/grouping-assign.system.md : system prompt: the input, key and output contracts, what does not split, answer rules
src/perfrepair/prompts/prompts.yaml : the prompt registry: name → file, lifetime, declared values
src/perfrepair/prompts/review.system.md : system prompt: accept, refuse with what the job got wrong, or unidentified; one tool call per reply
src/perfrepair/prompts/select.system.md : system prompt: choose one of code's candidates or none (a broken use: no none) with a reason; one tool call per reply
src/perfrepair/prompts/shared/rejection.turn.md : the turn message after a rejected answer
```
