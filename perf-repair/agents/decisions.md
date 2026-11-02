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
- commit: the outbox record is the only commit; state is `project(kind, records)` and `validate` must check it equals the saved state.
- journal: every turn is appended to `<dir>/journal.jsonl` with its `charter` fingerprint; audit only.
- settings: a key in `perfrepair.yaml` maps to an existing flag or constructor argument; a role default lives in `ROLE_DEFAULTS`, never in a command.
- settings: secrets stay in the environment or `.env`; the claude-code child never receives `ANTHROPIC_API_KEY`.
- prompts: read only through `PromptLibrary`; a changed prompt changes the charter fingerprint and starts a new outbox.

## Workflow
- add a role: copy the layout of `ai/suggest/site_replace/` into `ai/<role-kind>/<name>/`, one file per job:
  - `kind.py`: the DecisionKind (name, items, pending, empty, admit, label, render, check, apply, validate, write) and `charter(library)`; render calls `render.py`, check calls the gate, validate ends with `replay_problems`
  - `render.py`: the message text only
  - `schema.py`: the answer's JSON schema only
  - `state.py`: the role's projection type, when no dto type fits
  - `command.py`: the stage function the CLI calls, and its `DRY_RUN` conversations
  - gate C: `validation/<role-kind>/<name>.py`, and the state validator (`agents/validation.md`)
  - prompt file under `prompts/<role-kind>/` and its `prompts.yaml` entry
  - CLI subcommand → map lines → `docs/decisions.md`
- change a prompt: its gate and `docs/decisions.md` in the same change

## File structure

```
src/perfrepair/ai/__main__.py : command: the worthiness and replace stages
src/perfrepair/ai/evaluate/worthiness/command.py : stage: groups.json + measurements → evidence, triage, WorthinessKind on the engine
src/perfrepair/ai/evaluate/worthiness/kind.py : decision: test or skip a group's improving pairs; triage statics, apply, dropped → fallback skip
src/perfrepair/ai/evaluate/worthiness/render.py : message: mode, run warnings, members M1..Mn, per-configuration member and pair tables
src/perfrepair/ai/evaluate/worthiness/schema.py : answer schema: decision, pairs (from, to, reason), reason; all required
src/perfrepair/ai/runtime/agent/claude.py : Messages API client: whole message list per request, cached system prompt, JSON schema output, server-side refusal fallback
src/perfrepair/ai/runtime/agent/claude_code.py : Claude Code headless (`claude -p`) as Agent and Conversations: isolated sessions, --resume, existing login, no ANTHROPIC_API_KEY in the child
src/perfrepair/ai/runtime/agent/conversation.py : Conversation and Conversations: multi-turn agents; Claude and scripted
src/perfrepair/ai/runtime/agent/reply.py : Agent protocol, AgentReply, AgentRefused
src/perfrepair/ai/runtime/agent/select.py : --agent, --model, --effort per role → resolved agent settings → Conversations
src/perfrepair/ai/runtime/engine/ask.py : one item's asking: turns in a conversation, then fresh conversations
src/perfrepair/ai/runtime/engine/decide.py : the engine loop: pops pending items; gates, ask, durable commit, projections, journal, errors, --limit
src/perfrepair/ai/runtime/engine/journal.py : journal.jsonl append and read; audit only
src/perfrepair/ai/runtime/engine/kind.py : DecisionKind contract (items for lookup, pending to ask), project(kind, records), replay_problems: version count and replay equality
src/perfrepair/ai/runtime/engine/outbox.py : the only commit: durable, exclusive, ordered records per charter fingerprint; `active` pointer
src/perfrepair/ai/runtime/prompt/args.py : --prompts DIR on every model-calling command; one library load per invocation, PromptError exits 2
src/perfrepair/ai/runtime/prompt/library.py : PromptLibrary: reads prompts.yaml and the prompt files once, checks them, fills declared values
src/perfrepair/ai/suggest/site_replace/command.py : stage: apps/<app>/dossiers.json → SiteReplaceKind on the engine → replacements.json; dry run keeps
src/perfrepair/ai/suggest/site_replace/kind.py : decision: replace or keep one call site; a static keep per noOptions scope (reason = its code), gate, apply, dropped → fallback keep
src/perfrepair/ai/suggest/site_replace/render.py : message: site, scope facts, current, options R1..Rn with pins (or unknown), interop and the risk it adds, and estimates (n/a when n<2), edit kinds, fenced source
src/perfrepair/ai/suggest/site_replace/schema.py : answer schema: decision, option alias, edits, risks, reason; all required
src/perfrepair/ai/suggest/site_replace/state.py : Replacements: one Replacement and its source (llm, fallback, static) per scope
src/perfrepair/config/__init__.py : docstring only
src/perfrepair/config/args.py : --perfrepair-config; one settings load per command; unset flags filled, required ones checked
src/perfrepair/config/dotenv.py : .env reader: its PERFREPAIR_* keys as a layer; other keys fill unset environment keys
src/perfrepair/config/load.py : settings file lookup; layered resolution per key and per role, with each value's source
src/perfrepair/config/settings.py : perfrepair.yaml sections as frozen dataclasses: unknown_keys, invalid, secret_key; role sections and defaults
src/perfrepair/prompts/evaluate/worthiness.system.md : system prompt: test-worthiness
src/perfrepair/prompts/parse/algorithm-classify.system.md : system prompt: deprecated, accepted or unsure per listed id; when in doubt unsure; reason each
src/perfrepair/prompts/parse/grouping-assign.system.md : system prompt: interchangeability, identity vs capability, answer rules
src/perfrepair/prompts/prompts.yaml : the prompt registry: name → file, lifetime, declared values
src/perfrepair/prompts/review/grouping-review.system.md : supervisor system prompt: findings only
src/perfrepair/prompts/shared/rejection.turn.md : the turn message after a rejected answer
src/perfrepair/prompts/suggest/site-replace.system.md : system prompt: replace or keep a call site; like-for-like, risks (unverified interop is one), cite the metric
```
