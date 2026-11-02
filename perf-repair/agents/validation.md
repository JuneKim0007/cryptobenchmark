# Validation

## Calls
- `docs/artifacts.md` : which validator owns each artifact

## Rules
- coverage: every artifact and every decision state has a validator; a validator returns every problem, never only the first.
- gate: a stage calls `require` on its inputs and on its outputs; a failed gate stops the stage.
- projection: a decision state must equal the projection of its outbox (each kind's `validate`); static verdicts must equal triage.
- purity: validators read and compare; they never repair.

## Workflow
- add a validator: `validation/<artifact>.py` → `check/run.py` → export in `validation/__init__.py` → row in `docs/artifacts.md`
- check a run: `python3 -m perfrepair.validation <run dir>`

## File structure

```
src/perfrepair/check/run.py : stage replay: validate every artifact present in a run directory, rebuilding kinds from their outboxes
src/perfrepair/validation/__main__.py : command: validate a run directory; exit 1 on any problem, 2 on bad usage
src/perfrepair/validation/app.py : app.json and scopes.json: shape, contract values, recomputed scope ids; scope_problems shared with dossiers
src/perfrepair/validation/dossiers.py : the one dossiers.json validator: header, noOptions codes, check_dossier per dossier (interop labels in PAIR_STATUSES, never fail), every scope once, options from the current item's group with groups.json's interop status
src/perfrepair/validation/evaluate/worthiness.py : gate C of worthiness: a reply against its group's evidence, in aliases M1..Mn; pairs must improve under the mode
src/perfrepair/validation/failure.py : ValidationFailed and require: the stage gate
src/perfrepair/validation/grouping/interop.py : interop plan against groups, results against the plan, groups.json section, dossier options
src/perfrepair/validation/grouping/items.py : items.json and profiles.json
src/perfrepair/validation/grouping/knowledge.py : knowledge: well-formed groups, members in one group of their family
src/perfrepair/validation/grouping/output.py : groups.json: one group or dropped per item, consistent index
src/perfrepair/validation/json_reply.py : any model reply: JSON, and an object
src/perfrepair/validation/manifest.py : manifest: listed files exist, a counted key has its file, unique provider names, precedence 1..n
src/perfrepair/validation/measurements.py : measurements: known rows, ordered finite summaries, positive medians
src/perfrepair/validation/parse/grouping_assign.py : gate C of grouping-assign: an agent answer against its item and the knowledge
src/perfrepair/validation/repair.py : edits.json and harness.yaml: shape, reason codes, applied scopes only; EDIT_REASONS
src/perfrepair/validation/replacements.py : replacements: known scopes, a static keep with its code per noOptions scope, edits exactly the option's provider and pins, risks the scope and option imply
src/perfrepair/validation/report.py : report.json and summary.json: statuses, metric rows (no number without a measurement), funnel recount, app partition
src/perfrepair/validation/review/grouping_review.py : gate C of grouping-review: supervisor findings name only that family, arity per kind
src/perfrepair/validation/rows.py : rows: unique ids, identity present, positive sizes
src/perfrepair/validation/run_log.py : run log: measured rows exist, every other entry has a reason
src/perfrepair/validation/suggest/dossier.py : dossiers.json into Dossiers and noOptions for the replace stage, by the checks of validation/dossiers.py
src/perfrepair/validation/suggest/site_replace.py : gate C of site-replace: a reply against its dossier, in its aliases; refuses an option with unknown pins; risks from scope and option
src/perfrepair/validation/verdicts.py : verdicts: known groups, static equal triage, pairs are members
```
