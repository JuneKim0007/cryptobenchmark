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
- key contract: derived in `grouping/build/key_contract.py` from probe attributes, a generator's from its trial's produced key cross-checked with its provider's consumers; never from a provider name or a registered `KeyStore`; doubt is `unknown`, never a guess, and an unknown generator joins no group.
- classify: with `device.screening.aiReview` the build asks the classify model about unknown items only, before screen.json is written; `docs/screening.md` Model review.
- identified: a screened-out item or a name with a contract row in `catalog/groups.yaml` is placed without a model and never asked (`probe/identified.py`, the one test); every other item is one model call; `docs/grouping.md` Identified items.
- catalog: it and the signature exist only to reduce model calls; nothing writes it at run time; a person adds names from `group-candidates.yaml`.
- signature: evidence, never the decision: it derives the contract rows of listed names and checks groups; what splits a row is data in `catalog/interchange.yaml`, derived in `catalog/signature.py`; missing evidence is `unknown`, never the name's default.
- items: ids `1..n` per run; `items.json` is never edited after build; the agent sees one YAML block: the family, its groups (catalog and this run's) and the item, facts under input, key and output.
- commit: the outbox record is the commit; knowledge, cursor and errors are projections rebuilt from it; nothing writes knowledge directly.
- gates: A before every pop, B after it, C on every answer, D after every write; a failed gate stops the stage.
- families: a new family is a catalog entry, not code; descriptions in the catalog are immutable to agents.
- supervisor: findings only; it never edits a group.
- checks: a static finding is one function in `grouping/report/rules.py`.

## Workflow
- run: `build` (classify inside, with aiReview) → `assign` → `report [--supervisor]` → `interop-plan` → cryptobenchmark `--interop` → `interop-read` (`python3 -m perfrepair.grouping`); the guide's interop step does the last three through `device/interop.py`
- interop: a failed pair leaves evidence and dossier options; a `not_checkable` pair stays, labelled; a pair across key contracts is never planned, the plan marks it `not_checkable`; never edit a group for it.
- change the catalog: add the id `<type>|<canonical>` to its family in `catalog/groups.yaml` and its entry to `catalog/algorithms/<family>_catalogue.yaml`, checked by `validation/catalogue_entry.py`; a candidate is promoted by hand
- add a static check: function in `rules.py` → `RULES` → row in `docs/grouping.md`
- change the answer contract: `ai/parse/grouping_assign/schema.py` → `prompts/parse/grouping-assign.system.md` → `validation/parse/grouping_assign.py` → `docs/grouping.md`

## File structure

```
src/perfrepair/ai/parse/algorithm_classify/command.py : step of grouping build with device.screening.aiReview: batches.json, ClassifyKind on the engine, registry-candidates.yaml, reviewed verdicts; Reviewer; its dry run (unsure)
src/perfrepair/ai/parse/algorithm_classify/kind.py : ClassifyKind on the engine: one batch of unknown items per decision; the whole evidence as charter inputs; gate C, apply, validate
src/perfrepair/ai/parse/algorithm_classify/render.py : one batch's message: per id the engine type, name, canonical, provider, family, trial, className, attributes
src/perfrepair/ai/parse/algorithm_classify/schema.py : the answer's JSON schema: answers of id, answer, reason
src/perfrepair/ai/parse/algorithm_classify/state.py : Classified (the outbox's projection), reviewed (answers onto verdicts), candidates (registry-candidates.yaml)
src/perfrepair/ai/parse/grouping_assign/command.py : stage: assign; refresh; GroupingKind on the engine, its dry run
src/perfrepair/ai/parse/grouping_assign/kind.py : GroupingKind on the engine: askable (not identified), pending (askable, narrowed to used.json when present), not_used, code-made and catalog groups seeded in empty, a refresh token as charter inputs, gone (a record's item that left), admit (gate B), check (gate C), apply, validate (gates A, D), projections
src/perfrepair/ai/parse/grouping_assign/render.py : one item's message: one YAML block of the family, its groups and the item, each with the facts code knows by contract; exact leaves out each group a known fact contradicts
src/perfrepair/ai/parse/grouping_assign/schema.py : the answer's JSON schema; id patterns and description length from the gate's SLUG and MAX_DESCRIPTION
src/perfrepair/ai/parse/grouping_assign/state.py : the outbox's projections: cursor (next undecided pending item) and knowledge
src/perfrepair/ai/review/grouping_review/command.py : stage: report --supervisor: GroupingReviewKind on the engine under grouping/review; its dry run
src/perfrepair/ai/review/grouping_review/kind.py : decision: one item per family with a model-made group; the messages' hash as charter inputs; supervisor.json a projection of the outbox
src/perfrepair/ai/review/grouping_review/render.py : one family's review message
src/perfrepair/ai/review/grouping_review/schema.py : the supervisor's JSON schema; its kind enum is the review gate's KINDS
src/perfrepair/ai/review/grouping_review/state.py : Reviews: one result per reviewed family
src/perfrepair/catalog/algorithms.py : reader of the catalogues, checked whole: entry fields, provenance, sources, contracts, type facts, provider overrides; lookup by family and id
src/perfrepair/catalog/algorithms/ : data: `<family>_catalogue.yaml` per family, one entry per id `<type>|<canonical>` (key, required, optional, conditions, contract, sourcedOnly, providers, provenance); `common.yaml` sources, keyStrength maps, deterministicRelied
src/perfrepair/catalog/families.py : the family catalog and (engine type, key kind) → family
src/perfrepair/catalog/families.yaml : predefined families with fixed descriptions, the one copy
src/perfrepair/catalog/groups.py : reader of groups.yaml, checked whole: one group per family by id, contract rows from each member's catalogue contract, a row at each key contract
src/perfrepair/catalog/groups.yaml : data: one predefined group per family: its algorithm ids; a person adds ids from group-candidates.yaml
src/perfrepair/catalog/identity.py : one algorithm's ids: the registered item, the canonical algorithm, its contract row; a case id read back from its fields
src/perfrepair/catalog/interchange.py : reader of interchange.yaml: engines, rules by canonical name; a component outside its splits is refused
src/perfrepair/catalog/interchange.yaml : data: per engine type the components that split a group, the rules that read them from a canonical name, what a missing key contract means, and which contract each component states
src/perfrepair/catalog/key-contract.yaml : data: the key class prefixes that are standard interfaces, no provider's own; the standard format of a generated key per generator type
src/perfrepair/catalog/key_contract.py : reader of key-contract.yaml: the standard key interface prefixes, the generated key formats
src/perfrepair/catalog/resolved.py : the digest and MGF1 of a trial's `resolved` text, by canonical digest name
src/perfrepair/catalog/signature.py : an item's signature from its canonical name, resolved and key contract; known, convention or unknown per component
src/perfrepair/catalog/types.py : the catalogues' type facts as rows by family and canonical name; strength at a key size
src/perfrepair/catalog/views.py : what an agent is shown: one entry with only its provider's overrides (view_for), one group's description and ids (group_view)
src/perfrepair/grouping/__main__.py : command: build (screening catalog from perfrepair.yaml) | assign | report [--supervisor] | interop-plan | interop-read
src/perfrepair/grouping/build/items.py : benchmark documents → items and profiles, a declared transformation that ran being an item; ids in (family, name, provider) order
src/perfrepair/grouping/build/key_contract.py : key contract from probe attributes: a key format or a standard key interface → app_held; only other key classes → provider_held; neither → unknown; a generator's from its trial (standard format and encoded → app_held, no encoding → provider_held, else unknown) and cross_checked with its consumers
src/perfrepair/grouping/build/key_kind.py : key kind from recorded fields: measured → engine type → key generator → declared → unknown
src/perfrepair/grouping/build/stage.py : stage: manifest → items.json, profiles.json, screen.json (by the resolved catalog; classify first with a reviewer), validated, then written together with screen.json's `built` digests
src/perfrepair/grouping/interop_plan.py : groups.json, profiles.json, screen.json → interop_plan.yaml: every two runnable members of a group with two engines, once, at its own key size; with sites only those with a member a site resolves to; a pair across key contracts as not_checkable
src/perfrepair/grouping/interop_read.py : verdicts checked against the plan and written into grouping/: cryptobenchmark's interop.yaml, or the guide's merged document
src/perfrepair/grouping/report/candidates.py : group-candidates.yaml (schema 2) at report: model answers in the contract row shape plus provenance (model, run, item, date, checks); rebuilt from the outbox; nothing writes the catalog at run time
src/perfrepair/grouping/report/checks.py : stage: finished grouping → knowledge.json, checks.json, groups.json, group-candidates.yaml (`notUsed` with used.json); report_documents: what they should hold, nothing written
src/perfrepair/grouping/report/output.py : groups.json assembly; each item's screen status
src/perfrepair/grouping/report/rules.py : static checks over a finished grouping, key_contract_conflict among them
```
