# Grouping

## Calls
- `docs/grouping.md` : files, answer contract, gates, families, findings
- `agents/decisions.md` : agents, conversations and retry of the engine loop
- `agents/validation.md` : the validators the gates run

## Rules
- family: static; a catalog entry keyed by engine type + key kind.
- group: an agent's decision inside one family.
- capabilities: key size, tag length, key residency and availability are static; never group identity.
- classify: with `screening.aiReview` the build asks the classify model about unknown items only, before screen.json is written; `docs/screening.md` Model review.
- code-made: a screened-out item is grouped by code (`screen/groups.py`), never asked; `docs/grouping.md` Code-made groups.
- items: ids `1..n` per run; `items.json` is never edited after build; the agent sees `{id, type, name, provider, resolved}` and its family's groups only.
- commit: the outbox record is the commit; knowledge, cursor and errors are projections rebuilt from it; nothing writes knowledge directly.
- gates: A before every pop, B after it, C on every answer, D after every write; a failed gate stops the stage.
- families: a new family is a catalog entry, not code; descriptions in the catalog are immutable to agents.
- supervisor: findings only; it never edits a group.
- checks: a static finding is one function in `grouping/report/rules.py`.

## Workflow
- run: `build` (classify inside, with aiReview) → `assign` → `report [--supervisor]` → `interop-plan` → cryptobenchmark `--interop` → `interop-read` (`python3 -m perfrepair.grouping`)
- interop: a failed pair leaves evidence and dossier options; a `not_checkable` pair stays, labelled; never edit a group for it.
- add a static check: function in `rules.py` → `RULES` → row in `docs/grouping.md`
- change the answer contract: `ai/parse/grouping_assign/schema.py` → `prompts/parse/grouping-assign.system.md` → `validation/parse/grouping_assign.py` → `docs/grouping.md`

## File structure

```
src/perfrepair/ai/parse/algorithm_classify/command.py : step of grouping build with screening.aiReview: batches.json, ClassifyKind on the engine, registry-candidates.yaml, reviewed verdicts; Reviewer; its dry run (unsure)
src/perfrepair/ai/parse/algorithm_classify/kind.py : ClassifyKind on the engine: one batch of unknown items per decision; the whole evidence as charter inputs; gate C, apply, validate
src/perfrepair/ai/parse/algorithm_classify/render.py : one batch's message: per id the engine type, name, canonical, provider, family, trial, className, attributes
src/perfrepair/ai/parse/algorithm_classify/schema.py : the answer's JSON schema: answers of id, answer, reason
src/perfrepair/ai/parse/algorithm_classify/state.py : Classified (the outbox's projection), reviewed (answers onto verdicts), candidates (registry-candidates.yaml)
src/perfrepair/ai/parse/grouping_assign/command.py : stage: assign; GroupingKind on the engine, its dry run
src/perfrepair/ai/parse/grouping_assign/kind.py : GroupingKind on the engine: pending (not screened out), code-made groups seeded in empty, screen statuses as charter inputs, admit (gate B), check (gate C), apply, validate (gates A, D), projections
src/perfrepair/ai/parse/grouping_assign/render.py : one item's message: family, its groups, the item
src/perfrepair/ai/parse/grouping_assign/schema.py : the answer's JSON schema
src/perfrepair/ai/parse/grouping_assign/state.py : the outbox's projections: cursor (next undecided pending item) and knowledge
src/perfrepair/ai/review/grouping_review/command.py : stage: report --supervisor; charter, provenance, its dry run
src/perfrepair/ai/review/grouping_review/render.py : one family's review message
src/perfrepair/ai/review/grouping_review/run.py : supervisor: one review conversation per family with a model-made group → supervisor.json
src/perfrepair/ai/review/grouping_review/schema.py : the supervisor's JSON schema; its kind enum is the review gate's KINDS
src/perfrepair/catalog/families.py : the family catalog and (engine type, key kind) → family
src/perfrepair/catalog/families.yaml : predefined families with fixed descriptions
src/perfrepair/grouping/__main__.py : command: build (screening catalog from perfrepair.yaml) | assign | report [--supervisor] | interop-plan | interop-read
src/perfrepair/grouping/build/items.py : benchmark documents → items and profiles; ids in (family, name, provider) order
src/perfrepair/grouping/build/key_kind.py : key kind from recorded fields: measured → engine type → key generator → declared → unknown
src/perfrepair/grouping/build/stage.py : stage: manifest → items.json, profiles.json, screen.json (by the resolved catalog; classify first with a reviewer), validated before writing
src/perfrepair/grouping/interop_plan.py : groups.json → interop_plan.yaml: every two runnable members of a group, once
src/perfrepair/grouping/interop_read.py : cryptobenchmark's interop.yaml checked against the plan and imported into grouping/
src/perfrepair/grouping/report/checks.py : stage: finished grouping → checks.json, groups.json
src/perfrepair/grouping/report/output.py : groups.json assembly; each item's screen status
src/perfrepair/grouping/report/rules.py : static checks over a finished grouping
```
