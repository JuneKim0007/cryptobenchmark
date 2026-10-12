# Decisions

## Calls
- `docs/decisions.md` : what each decision sees, its answer, its gate
- `agents/validation.md` : the validator every decision state needs

## Rules
- role: a model call decides one item; it never computes, filters, lists or writes code.
- context: one fresh single-turn request per item: system prompt + the item's rendered message; no history.
- input: a rendered message carries only what the decision needs; assignment never sees timings.
- ids: code mints and resolves every id; the model answers with names from the message (`G00n`, `M1`).
- gate: every answer passes the kind's `validate` before `apply`; a refused answer is asked once more with the reasons, then the kind's `fallback` applies.
- static first: an item code can settle (triage) never reaches the model.
- commit: the outbox record is the only commit; state is `project(kind, records)` and `validate` must check it equals the saved state.
- journal: every turn is appended to `<dir>/journal.jsonl`; audit only.

## Workflow
- add a decision: a DecisionKind (items, empty, admit, render, check, apply, validate, write) → prompt → command calling `engine/decide.py` → structure validator (`agents/validation.md`) → `docs/decisions.md`
- change a prompt: its gate and `docs/decisions.md` in the same change

## File structure

```
src/perfrepair/orchestrate/__main__.py : command: the worthiness stage
src/perfrepair/orchestrate/agent/claude.py : Messages API agent: single turn, cached system prompt, JSON schema output, refusal fallback
src/perfrepair/orchestrate/agent/claude_code.py : Claude Code headless (`claude -p`) as Agent and Conversations: isolated sessions, --resume, existing login
src/perfrepair/orchestrate/agent/conversation.py : Conversation and Conversations: multi-turn agents; Claude and scripted
src/perfrepair/orchestrate/agent/reply.py : Agent protocol, AgentReply, AgentRefused
src/perfrepair/orchestrate/agent/select.py : --agent backend name → Agent or Conversations
src/perfrepair/orchestrate/commands/worthiness.py : stage: groups.json + measurements → evidence, triage, WorthinessKind on the engine
src/perfrepair/orchestrate/decisions/worthiness.py : decision: test or skip a group's improving pairs; render, gate, apply, fallback
src/perfrepair/orchestrate/engine/ask.py : one item's asking: turns in a conversation, then fresh conversations
src/perfrepair/orchestrate/engine/decide.py : the engine loop: gates, ask, durable commit, projections, journal, errors, --limit
src/perfrepair/orchestrate/engine/kind.py : DecisionKind contract and project(kind, records)
src/perfrepair/orchestrate/engine/outbox.py : the only commit: durable, exclusive, ordered outbox records
src/perfrepair/orchestrate/journal.py : journal.jsonl append and read; audit only
src/perfrepair/orchestrate/prompts/worthiness.system.md : system prompt: test-worthiness
```
