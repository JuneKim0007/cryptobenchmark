# Validation

## Calls
- `docs/artifacts.md` : which validator owns each artifact

## Rules
- coverage: every artifact and every decision state has a validator; a validator returns every problem, never only the first.
- gate: a stage calls `require` on its inputs and on its outputs; a failed gate stops the stage.
- replay: a decision state must equal the projection of its outbox (each kind's `validate`); static verdicts must equal triage.
- purity: validators read and compare; they never repair.

## Workflow
- add a validator: `validation/<artifact>.py` → `validation/run.py` → export in `validation/__init__.py` → row in `docs/artifacts.md`
- check a run: `python3 -m perfrepair.validation <run dir>`

## File structure

```
src/perfrepair/validation/__main__.py : command: validate a run directory; exit 1 on any problem
src/perfrepair/validation/failure.py : ValidationFailed and require: the stage gate
src/perfrepair/validation/grouping/answer.py : gate C: an agent answer against its item and the knowledge
src/perfrepair/validation/grouping/items.py : items.json and profiles.json
src/perfrepair/validation/grouping/knowledge.py : knowledge: well-formed groups, members in one group of their family
src/perfrepair/validation/grouping/output.py : groups.json: one group or dropped per item, consistent index
src/perfrepair/validation/grouping/supervision.py : supervisor findings: name only that family, arity per kind
src/perfrepair/validation/json_reply.py : any model reply: JSON, and an object
src/perfrepair/validation/manifest.py : manifest: files exist, precedence 1..n, counts match files
src/perfrepair/validation/measurements.py : measurements: known rows, ordered finite summaries, positive medians
src/perfrepair/validation/repair.py : a patch changes only string literals of the call on its line
src/perfrepair/validation/rows.py : rows: unique ids, identity present, positive sizes
src/perfrepair/validation/run.py : validate every artifact present in a run directory
src/perfrepair/validation/run_log.py : run log: measured rows exist, every other entry has a reason
src/perfrepair/validation/worthiness.py : verdicts: one per group, static equal triage, pairs are members
```
