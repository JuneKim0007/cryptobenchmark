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
- check a device folder: `python3 -m perfrepair.validation --device-results <device>`

## File structure

```
src/perfrepair/check/run.py : stage replay: validate every artifact present in a device folder (each outbox's charter.json rehashed to its folder name, supervisor.charter.json, events.jsonl) (a malformed rows, measurements or run log file is its problem); primitives.tsv against rows, measurements and screen.json, rebuilding kinds from their outboxes, each worthiness-<perfMode> folder under its own perfMode; screen.json against the resolved catalog; used.json against items.json; the classify outbox, classified.json, model verdicts and registry-candidates.yaml when screen.json was reviewed
src/perfrepair/validation/__main__.py : command: validate a device folder by the resolved screening catalog (`--perfrepair-config`); exit 1 on any problem, 2 on bad usage or a missing catalog
src/perfrepair/validation/answer_text.py : text rules answer schemas share: not blank, empty or a pattern, alias patterns
src/perfrepair/validation/app.py : app.json and scopes.json: shape, contract values, recomputed scope ids and patterns; scope_problems shared with dossiers
src/perfrepair/validation/bundled.py : bundled-suggestions.yaml: counts equal the lists, a matched row's entry at its pinned version, a blocked or unmatched row has a reason and no entry, only apply applies
src/perfrepair/validation/classified.py : classify/classified.json: answers only for batched ids, ids in one batch, allowed values, a reason each
src/perfrepair/validation/dossier_units.py : dossiers.json against units.json: every unit with a member with options asked, with its stays and pairs; `provider_held_key` exactly where a member's key contract is provider-held
src/perfrepair/validation/dossiers.py : the one dossiers.json validator: header with its perfMode, noOptions codes, estimates of selected metrics only, check_dossier per dossier (interop labels in PAIR_STATUSES, never fail), every scope once, options from the current item's group with groups.json's interop status, the app's screen status, never lowering the status; parse_dossiers: units with their Dossiers and noOptions for the replace stage, by the same checks
src/perfrepair/validation/evaluate/worthiness.py : gate C of worthiness: a reply against its group's evidence, in aliases M1..Mn; pairs must improve under the mode
src/perfrepair/validation/events.py : log/events.jsonl through read_jsonl: every whole line JSON (a cut one skipped), schema 1, every field with its type, a known kind; a partial last line
src/perfrepair/validation/failure.py : ValidationFailed and require: the stage gate
src/perfrepair/validation/grouping/code_groups.py : code-made groups equal the ones screen.json and the signatures imply; no item grouped by code in a model group
src/perfrepair/validation/grouping/interop.py : interop plan against groups, results against the plan, groups.json section, dossier options
src/perfrepair/validation/grouping/items.py : items.json and profiles.json
src/perfrepair/validation/grouping/knowledge.py : knowledge: well-formed groups, members in one group of their family
src/perfrepair/validation/grouping/output.py : groups.json (schema 3): one group or dropped per item, consistent index, `screen` equal to screen.json, code-made groups; read_groups reads it gated
src/perfrepair/validation/json_reply.py : any model reply: JSON, and an object
src/perfrepair/validation/manifest.py : manifest: listed files exist, a counted key has its file, unique provider names, precedence 1..n
src/perfrepair/validation/measurements.py : measurements: known rows, registry metrics only, required ones present, ordered finite summaries, positive medians and kinds as the registry says
src/perfrepair/validation/parse/algorithm_classify.py : gate C of algorithm-classify: one answer per listed id, allowed values, a reason
src/perfrepair/validation/parse/grouping_assign.py : gate C of grouping-assign: an agent answer against its item, the knowledge and the signatures
src/perfrepair/validation/primitives.py : primitives.tsv: unique lines, registry metric columns, screen statuses, each metric's n, and equal line for line to what rows, measurements and screen.json make
src/perfrepair/validation/repair.py : edits.json and harness.yaml: shape, reason codes, applied scopes only; EDIT_REASONS; `valid_inputs`, also used by the report check
src/perfrepair/validation/replacements.py : replacements: known scopes, a static keep with its code per noOptions scope, edits exactly the option's provider and pins, risks the scope and option imply; consistent_units
src/perfrepair/validation/report.py : report.json and summary.json: statuses, metric rows (no number without a measurement, selected as the mode says), funnel recount, app partition per pattern, each row's pattern and categoryMismatch recomputed, pattern counts
src/perfrepair/validation/review/grouping_review.py : gate C of grouping-review: KINDS, whose order feeds the review schema and its fingerprint; supervisor findings name only that family, arity per kind
src/perfrepair/validation/rows.py : rows: unique ids, identity present, positive sizes, a known variant
src/perfrepair/validation/run_log.py : run log: measured rows exist, every other entry has a reason
src/perfrepair/validation/screen.py : screen.json: built from this run's items.json and profiles.json (`built` digests), its catalog identity `{source, sha256}`, one verdict per item id, statuses in the set, a source for every status but unknown, a canonical name for a never-target one, a model source for unverified, and a model source only as `model:<review fingerprint>`; validate_model_verdicts: model-sourced verdicts equal the classify answers; read_checked_screen: the gated reader assign and read_groups use
src/perfrepair/validation/suggest/site_performance.py : the replacement gate's performance part: a listed perfMode's strict rule, generic's named deciding metrics and accepted losses over the code labels; recommend's change line and needs; concerns' length
src/perfrepair/validation/suggest/site_replace.py : gate C of site-replace: a reply against its unit, member by member in their aliases; the members with options all replaced or all kept, none that stays named; an inverse pair's interop; refuses an option with unknown pins; risks from scope and option
src/perfrepair/validation/units.py : units.json: every scope in one unit, ids recomputed, members connected, each cited line in that side's lifecycle
src/perfrepair/validation/used.py : used.json: each item a device item named once, a known via, apps it lists, matched within sites, deviceItems equal to items.json
src/perfrepair/validation/verdicts.py : verdicts: known groups, static equal triage, pairs are members
```
