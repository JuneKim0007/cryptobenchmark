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
src/perfrepair/ai/__main__.py : command: the worthiness stage
src/perfrepair/ai/evaluate/worthiness/command.py : stage: groups.json + measurements → evidence, triage, WorthinessKind on the engine
src/perfrepair/ai/evaluate/worthiness/kind.py : decision: test or skip a group's improving pairs; render, gate, apply, fallback
src/perfrepair/ai/runtime/agent/claude.py : Messages API agent: single turn, cached system prompt, JSON schema output, refusal fallback
src/perfrepair/ai/runtime/agent/claude_code.py : Claude Code headless (`claude -p`) as Agent and Conversations: isolated sessions, --resume, existing login
src/perfrepair/ai/runtime/agent/conversation.py : Conversation and Conversations: multi-turn agents; Claude and scripted
src/perfrepair/ai/runtime/agent/reply.py : Agent protocol, AgentReply, AgentRefused
src/perfrepair/ai/runtime/agent/select.py : --agent backend name → Agent or Conversations
src/perfrepair/ai/runtime/engine/ask.py : one item's asking: turns in a conversation, then fresh conversations
src/perfrepair/ai/runtime/engine/decide.py : the engine loop: gates, ask, durable commit, projections, journal, errors, --limit
src/perfrepair/ai/runtime/engine/journal.py : journal.jsonl append and read; audit only
src/perfrepair/ai/runtime/engine/kind.py : DecisionKind contract and project(kind, records)
src/perfrepair/ai/runtime/engine/outbox.py : the only commit: durable, exclusive, ordered outbox records
src/perfrepair/ai/runtime/prompt/library.py : PromptLibrary: reads prompts.yaml and the prompt files once, checks them, fills declared values
src/perfrepair/prompts/evaluate/worthiness.system.md : system prompt: test-worthiness
src/perfrepair/prompts/parse/grouping-assign.system.md : system prompt: interchangeability, identity vs capability, answer rules
src/perfrepair/prompts/prompts.yaml : the prompt registry: name → file, lifetime, declared values
src/perfrepair/prompts/review/grouping-review.system.md : supervisor system prompt: findings only
src/perfrepair/prompts/shared/rejection.turn.md : the turn message after a rejected answer
```
