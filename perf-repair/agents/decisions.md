# Decisions

## Calls
- `docs/decisions.md` : the engine's retry and model defaults; what the worthiness decision sees, answers, and its gate
- `agents/validation.md` : the validator every decision state needs
- `docs/settings.md` : perfrepair.yaml and .env: lookup, precedence, keys, roles

## Rules
- role: a model call decides one item.
- context: items are context-free: each session starts from the system prompt + the item's TaskPrompt; later turns in a session carry only CorrectionPrompts.
- input: a rendered message carries only what the decision needs; assignment never sees timings.
- ids: code mints item ids and member aliases (`M1..Mn`) and resolves them; a grouping answer mints a new group id, checked by gate C.
- gate: every answer passes the kind's `check` before `apply`.
- retry: a rejected answer gets a correction turn in the same session (`--turns`); a refusal ends the session; the next session re-sends the task (`--sessions`); then the item is committed as `dropped`.
- static first: an item code can settle (triage) never reaches the model.
- spawn: an agent starts one way: the role's kind builds its charter from `PromptLibrary`, `ai/runtime/gateway/spawn` gives the conversations, `ai/runtime/engine` opens one fresh conversation per item with the kind's rendered knowledge; `tests/test_layers.py` refuses any other path.
- log: a stage reports through `log/emit.py` (`step`, `emit`), never its own format.
- select, never aggregate: code reads, joins and stores the data (scopes, benchmark rows, groups, dossiers); a model chooses among the stored options by alias for one item and never reads raw benchmark data or computes a number.
- commit: the outbox record is the only commit; state is `project(kind, records)` and `validate` must check it equals the saved state.
- journal: every turn is appended to `<dir>/journal.jsonl` with its `charter` fingerprint; audit only.
- settings: a key in `perfrepair.yaml` is a row in `inputs/table.py` with exactly one reader, and ships only with the code that reads it; a role default lives in its `RoleRow`, never in a command.
- settings: `OnInvalid.ERROR` only where a fallback is unsafe; a bad flag always errors.
- settings: secrets stay in the environment or `.env`; the child of `auth: subscription` never receives `ANTHROPIC_API_KEY`.
- gateway: provider differences (schema stripping, child environment, CLI flags, effort levels) stay inside its modules under `ai/runtime/gateway/`; the engine and `Conversations` name no provider.
- gateway: a setting ships with the code that reads it; no block or stub for a provider without a gateway.
- gateway: every model command calls `gateway/spawn.py` before its work.
- prompts: read only through `PromptLibrary`; a changed prompt changes the charter fingerprint and starts a new outbox.

## Workflow
- add a role: copy the layout of `ai/suggest/site_replace/` into `ai/<role-kind>/<name>/`, one file per job:
  - `kind.py`: the DecisionKind (name, items, pending, empty, admit, label, render, check, apply, validate, write) and `charter(library)`; render calls `render.py`, check calls the gate, validate ends with `replay_problems`
  - `render.py`: the message text only
  - `schema.py`: the answer's JSON schema only; every limit its gate checks (length, pattern, enum) read from the gate's constants
  - `state.py`: the role's projection type, when no dto type fits
  - `command.py`: the stage function the CLI calls, and its `DRY_RUN` conversations
  - gate C: `validation/<role-kind>/<name>.py`, and the state validator (`agents/validation.md`)
  - prompt file under `prompts/<role-kind>/` and its `prompts.yaml` entry
  - CLI subcommand → map lines → `docs/decisions.md`
- change a prompt: its gate and `docs/decisions.md` in the same change
- add a provider: `ai/runtime/gateway/<name>.py` with a `Gateway` (settings dataclass, secret, spawn) → its row in `registry.py` → map line → `docs/settings.md`

## File structure

```
src/perfrepair/ai/__main__.py : command: the worthiness and replace stages
src/perfrepair/ai/evaluate/worthiness/command.py : stage: groups.json + measurements → evidence, triage, WorthinessKind on the engine
src/perfrepair/ai/evaluate/worthiness/kind.py : decision: test or skip a group's improving pairs; triage statics, apply, dropped → fallback skip
src/perfrepair/ai/evaluate/worthiness/render.py : message: mode, run warnings, members M1..Mn, per-configuration member and pair tables
src/perfrepair/ai/evaluate/worthiness/schema.py : answer schema: decision, pairs (from, to, reason), reason; all required; member aliases and non-blank reasons as patterns
src/perfrepair/ai/runtime/agent/conversation.py : Conversation and Conversations: the multi-turn protocol, its lifetime guard, scripted answers
src/perfrepair/ai/runtime/agent/reply.py : AgentReply, AgentRefused, AgentFailed (a provider's one coded failure line)
src/perfrepair/ai/runtime/engine/ask.py : one item's asking: turns in a conversation, then fresh conversations; each turn's model latency
src/perfrepair/ai/runtime/engine/charter_file.py : an outbox's charter.json: written once, checked on each open (`charter_mismatch`), rehashed by the validator; a recorded charter's inputs
src/perfrepair/ai/runtime/engine/decide.py : the engine loop: pops pending items; gates, ask, durable commit, projections, journal, errors, --limit, `mixed_agents`; start, turn, decision and end events
src/perfrepair/ai/runtime/engine/events.py : Where (stage, step, app); TurnEvents: each model turn and decision as an event with tokens, cost, latency and its journal line or outbox record
src/perfrepair/ai/runtime/engine/journal.py : journal.jsonl append, line count and read; audit only
src/perfrepair/ai/runtime/engine/kind.py : DecisionKind contract (items for lookup, pending to ask, optional gone and evidence_digest), item_of, evidence_of, project(kind, records), replay_problems: version count and replay equality
src/perfrepair/ai/runtime/engine/outbox.py : the only commit: durable, exclusive, ordered records per charter fingerprint; charter.json before the first record; `active` pointer; carry: another outbox's records into a charter's
src/perfrepair/ai/runtime/engine/refresh.py : --refresh run inputs (`refresh <token>`) and the active outbox's kept ones
src/perfrepair/ai/runtime/gateway/args.py : --agent, --auth, --model, --effort per role, with each role's default and the gateways' choices in the help
src/perfrepair/ai/runtime/gateway/claude.py : the claude gateway: ClaudeSettings (auth, model, effort, binary; its effort levels), the secret auth api needs, spawn by auth
src/perfrepair/ai/runtime/gateway/claude_api.py : Messages API transport: whole message list per request, cached system prompt, JSON schema output without the keywords the API refuses (`API_UNSUPPORTED`), server-side refusal fallback
src/perfrepair/ai/runtime/gateway/claude_cli.py : Claude CLI headless (`claude -p`) transport: isolated sessions, --resume, existing login, no ANTHROPIC_API_KEY or ANTHROPIC_AUTH_TOKEN in the child; ClaudeCliError `claude_cli_failed`, a CLI that cannot run included
src/perfrepair/ai/runtime/gateway/contract.py : Gateway: what one provider declares: name, settings class, spawn, secret, choices
src/perfrepair/ai/runtime/gateway/dry_run.py : the dry-run gateway: no keys, answers with the role's stand-in
src/perfrepair/ai/runtime/gateway/registry.py : name → Gateway; the default gateway; `unknown_gateway`
src/perfrepair/ai/runtime/gateway/spawn.py : the one spawn handler: role → gateway → every block checked (each key by the gateway's settings class) and resolved values → secret check → Conversations with their AgentIdentity
src/perfrepair/ai/runtime/prompt/args.py : --prompts DIR on every model-calling command; the one reader of `paths.prompts`; one library load per invocation, PromptError exits 2
src/perfrepair/ai/runtime/prompt/library.py : PromptLibrary: reads prompts.yaml and the prompt files once, checks them, fills declared values; each prompt's origin, `packaged` or its override file
src/perfrepair/ai/suggest/site_replace/command.py : stage: <app>/dossiers.json → SiteReplaceKind on the engine → replacements.json; dry run keeps; --refresh carries all but the stale records into a new outbox; dossier_changed
src/perfrepair/ai/suggest/site_replace/kind.py : decision: replace or keep one call site; a static keep per noOptions scope (reason = its code), gate, apply, dropped → fallback keep; evidence digest per dossier, stale, gone scopes
src/perfrepair/ai/suggest/site_replace/render.py : message: site, scope facts, current, options R1..Rn with pins (or unknown), interop and the risk it adds, and estimates (n/a when n<2), edit kinds, fenced source
src/perfrepair/ai/suggest/site_replace/schema.py : answer schema: decision, option alias, edits, risks, reason; all required; option alias (or empty) and non-blank reason as patterns
src/perfrepair/ai/suggest/site_replace/state.py : Replacements: one Replacement and its source (llm, fallback, static) per scope; the stale scopes
src/perfrepair/config/__init__.py : docstring only
src/perfrepair/config/args.py : --perfrepair-config; one settings load per command; unset flags filled from their rows, required ones checked; positive_int, the argparse type of --turns, --sessions, --limit
src/perfrepair/config/device_results.py : the device folder of a command: --device-results, else paths.results with device.id or its only device, their one reader; device_root (the root the guide hands to probe_device); not_device_results; the temporary-folder warning
src/perfrepair/config/dotenv.py : .env reader: its PERFREPAIR_* keys as a layer; other keys fill unset environment keys
src/perfrepair/config/load.py : settings file lookup; read a row, or a role's key, by its chain; each value's source, logged once (INFO from a file or the environment, else DEBUG)
src/perfrepair/config/settings.py : reads perfrepair.yaml: secret_key anywhere, unknown_key warnings from the rows' keys, a section's shape; raw values and aiGateway blocks
src/perfrepair/prompts/evaluate/worthiness.system.md : system prompt: test-worthiness
src/perfrepair/prompts/parse/algorithm-classify.system.md : system prompt: deprecated, accepted or unsure per listed id; when in doubt unsure; reason each
src/perfrepair/prompts/parse/grouping-assign.system.md : system prompt: the input, key and output contracts, what does not split, answer rules
src/perfrepair/prompts/prompts.yaml : the prompt registry: name → file, lifetime, declared values
src/perfrepair/prompts/review/grouping-review.system.md : supervisor system prompt: the three contracts; findings only
src/perfrepair/prompts/shared/rejection.turn.md : the turn message after a rejected answer
src/perfrepair/prompts/suggest/site-replace.system.md : system prompt: replace or keep a call site; like-for-like, risks (unverified interop is one), cite the metric
```
