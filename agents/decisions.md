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
- journal: every call is appended to `<kind>.journal.jsonl` with the message, reply, status and decision.

## Workflow
- add a single-call decision: kind in `decisions/` → prompt in `prompts/` → command in `commands/` → validator with replay (`agents/validation.md`) → section in `docs/decisions.md`; a multi-turn decision follows `agents/grouping.md`
- change a prompt: its gate and `docs/decisions.md` in the same change

## File structure

```
src/perfrepair/orchestrate/__main__.py : command: the worthiness stage
src/perfrepair/orchestrate/agent/claude.py : Messages API agent: single turn, cached system prompt, JSON schema output, refusal fallback
src/perfrepair/orchestrate/agent/conversation.py : Conversation and Conversations: multi-turn agents; Claude and scripted
src/perfrepair/orchestrate/agent/reply.py : Agent protocol, AgentReply, AgentRefused
src/perfrepair/orchestrate/agent/stand_ins.py : FixedAgent (dry run), ScriptedAgent (tests)
src/perfrepair/orchestrate/commands/worthiness.py : stage: registry + measurements → evidence, triage, verdicts per mode; gated
src/perfrepair/orchestrate/decisions/kind.py : DecisionKind contract and Checked
src/perfrepair/orchestrate/decisions/worthiness.py : decision: test or skip a group's improving pairs; render, gate, apply, fallback
src/perfrepair/orchestrate/journal.py : journal.jsonl append and read
src/perfrepair/orchestrate/prompts/worthiness.system.md : system prompt: test-worthiness
src/perfrepair/orchestrate/queue.py : file-backed FIFO of decision items; resumable
src/perfrepair/orchestrate/runner.py : generic loop: pop, ask, gate, apply, journal, save
```
