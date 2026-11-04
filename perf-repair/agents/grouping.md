# Grouping

## Calls
- `docs/grouping.md` : files, answer contract, gates, families, findings
- `docs/signature.md` : the signature's components and what each status does to an item
- `agents/decisions.md` : agents, conversations and retry of the engine loop
- `agents/validation.md` : the validators the gates run

## Rules
- family: static; a catalog entry keyed by engine type + key kind.
- group: an agent's decision inside one family.
- criterion: input, key and output contracts inside one family; `docs/grouping.md` Criterion.
- capabilities: key size, tag length and availability are static; never group identity.
- key contract: derived in `grouping/build/key_contract.py` from probe attributes; never from a provider name or a registered `KeyStore`; no attribute is `unknown`, never a guess.
- classify: with `device.screening.aiReview` the build asks the classify model about unknown items only, before screen.json is written; `docs/screening.md` Model review.
- code-made: a screened-out item or one with a decided signature is grouped by code (`screen/groups.py`), never asked; `docs/grouping.md` Code-made groups.
- signature: what splits a group is data in `catalog/interchange.yaml`, derived in `grouping/signature.py`; missing evidence is `unknown`, never the name's default; a rule moved to `convention` needs a real run's groups that support it.
- items: ids `1..n` per run; `items.json` is never edited after build; the agent sees `{id, type, name, provider, resolved, signature, key}` and its family's groups with their signature and key lines only.
- commit: the outbox record is the commit; knowledge, cursor and errors are projections rebuilt from it; nothing writes knowledge directly.
- gates: A before every pop, B after it, C on every answer, D after every write; a failed gate stops the stage.
- families: a new family is a catalog entry, not code; descriptions in the catalog are immutable to agents.
- supervisor: findings only; it never edits a group.
- checks: a static finding is one function in `grouping/report/rules.py`.

## Workflow
- run: `build` (classify inside, with aiReview) → `assign` → `report [--supervisor]` → `interop-plan` → cryptobenchmark `--interop` → `interop-read` (`python3 -m perfrepair.grouping`)
- interop: a failed pair leaves evidence and dossier options; a `not_checkable` pair stays, labelled; a pair across key contracts is never planned, the plan marks it `not_checkable`; never edit a group for it.
- add a static check: function in `rules.py` → `RULES` → row in `docs/grouping.md`
- change the answer contract: `ai/parse/grouping_assign/schema.py` → `prompts/parse/grouping-assign.system.md` → `validation/parse/grouping_assign.py` → `docs/grouping.md`

## File structure

```
src/perfrepair/ai/parse/algorithm_classify/command.py : step of grouping build with device.screening.aiReview: batches.json, ClassifyKind on the engine, registry-candidates.yaml, reviewed verdicts; Reviewer; its dry run (unsure)
src/perfrepair/ai/parse/algorithm_classify/kind.py : ClassifyKind on the engine: one batch of unknown items per decision; the whole evidence as charter inputs; gate C, apply, validate
src/perfrepair/ai/parse/algorithm_classify/render.py : one batch's message: per id the engine type, name, canonical, provider, family, trial, className, attributes
src/perfrepair/ai/parse/algorithm_classify/schema.py : the answer's JSON schema: answers of id, answer, reason
src/perfrepair/ai/parse/algorithm_classify/state.py : Classified (the outbox's projection), reviewed (answers onto verdicts), candidates (registry-candidates.yaml)
src/perfrepair/ai/parse/grouping_assign/command.py : stage: assign; rekey, refresh; GroupingKind on the engine, its dry run
src/perfrepair/ai/parse/grouping_assign/kind.py : GroupingKind on the engine: askable (not grouped by code), pending (askable, narrowed to used.json when present), not_used, code-made groups seeded in empty, a refresh token as charter inputs, gone (a record's item that left), admit (gate B), check (gate C), apply, validate (gates A, D), projections
src/perfrepair/ai/parse/grouping_assign/rekey.py : one move of an outbox whose records name positions to one naming Item.key, when its old charter still hashes to its name
src/perfrepair/ai/parse/grouping_assign/render.py : one item's message: family, its groups with their signature and key lines, the item with its signature and key line
src/perfrepair/ai/parse/grouping_assign/schema.py : the answer's JSON schema; id patterns and description length from the gate's SLUG and MAX_DESCRIPTION
src/perfrepair/ai/parse/grouping_assign/state.py : the outbox's projections: cursor (next undecided pending item) and knowledge
src/perfrepair/ai/review/grouping_review/command.py : stage: report --supervisor; charter, provenance, its dry run
src/perfrepair/ai/review/grouping_review/render.py : one family's review message
src/perfrepair/ai/review/grouping_review/run.py : supervisor: one review conversation per family with a model-made group → supervisor.json, its charter in supervisor.charter.json
src/perfrepair/ai/review/grouping_review/schema.py : the supervisor's JSON schema; its kind enum is the review gate's KINDS
src/perfrepair/catalog/families.py : the family catalog and (engine type, key kind) → family
src/perfrepair/catalog/families.yaml : predefined families with fixed descriptions
src/perfrepair/catalog/interchange.py : reader of interchange.yaml: engines, rules by canonical name; a component outside its splits is refused
src/perfrepair/catalog/interchange.yaml : data: per engine type the components that split a group, the rules that read them from a canonical name, and what a missing key contract means
src/perfrepair/catalog/key-contract.yaml : data: the key class prefixes that are standard interfaces, no provider's own
src/perfrepair/catalog/key_contract.py : reader of key-contract.yaml: the standard key interface prefixes
src/perfrepair/catalog/types.py : reader of types.yaml, checked whole: fields, sources, families, keyStrength maps; lookup by family and canonical name; strength at a key size
src/perfrepair/catalog/types.yaml : data: per family and canonical name the output kind, properties, strengthBits (SP 800-57) and minSdk (Android reference), each sourced
src/perfrepair/grouping/__main__.py : command: build (screening catalog from perfrepair.yaml) | assign | report [--supervisor] | interop-plan | interop-read
src/perfrepair/grouping/build/items.py : benchmark documents → items and profiles, a declared transformation that ran being an item; ids in (family, name, provider) order
src/perfrepair/grouping/build/key_contract.py : key contract from probe attributes: a key format or a standard key interface → app_held; only other key classes → provider_held; neither → unknown
src/perfrepair/grouping/build/key_kind.py : key kind from recorded fields: measured → engine type → key generator → declared → unknown
src/perfrepair/grouping/build/stage.py : stage: manifest → items.json, profiles.json, screen.json (by the resolved catalog; classify first with a reviewer), validated, then written together with screen.json's `built` digests
src/perfrepair/grouping/interop_plan.py : groups.json → interop_plan.yaml: every two runnable members of a group, once; a pair across key contracts as not_checkable
src/perfrepair/grouping/interop_read.py : cryptobenchmark's interop.yaml checked against the plan and imported into grouping/
src/perfrepair/grouping/report/checks.py : stage: finished grouping → knowledge.json, checks.json, groups.json (`notUsed` with used.json); report_documents: what they should hold, nothing written
src/perfrepair/grouping/report/output.py : groups.json assembly; each item's screen status
src/perfrepair/grouping/report/rules.py : static checks over a finished grouping
src/perfrepair/grouping/resolved.py : the digest and MGF1 of a trial's `resolved` text, by canonical digest name
src/perfrepair/grouping/signature.py : an item's signature from its canonical name, resolved and key contract; known, convention or unknown per component
```
