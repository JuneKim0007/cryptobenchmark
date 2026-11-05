# Validation

## Calls
- `docs/artifacts.md` : which validator owns each artifact
- `docs/invariants.md` : the grouping and scoping invariants, their severities and the command

## Rules
- coverage: every artifact and every decision state has a validator; a validator returns every problem, never only the first.
- gate: a stage calls `require` on its inputs and on its outputs; a failed gate stops the stage.
- projection: a decision state must equal the projection of its outbox (each kind's `validate`); static verdicts must equal triage.
- purity: validators read and compare; they never repair.
- rebuild: a role's file equals the rebuild of its outbox byte for byte (`rebuild_problems`); no parallel validator, the replay holds it.
- invariants: one `Violation` shape (`validation/finding.py`); blocking only where the artifact is wrong, undecided where the source does not tell, never a guess.

## Workflow
- add a validator: `validation/<artifact>.py` → `check/run.py` → export in `validation/__init__.py` → row in `docs/artifacts.md`
- check a device folder: `python3 -m perfrepair.validation --device-results <device>`
- check its invariants: `python3 -m perfrepair.validation.invariants <device>`

## File structure

```
src/perfrepair/check/apps.py : each app's dossiers.json against its scopes.json, units.json, groups.json and the app's screen verdicts; replacements.json against its dossiers and outbox, upgrades.json against its outbox, review/stability.json against its outbox, edits.json against its scopes, harness.yaml against its edits
src/perfrepair/check/contracts.py : each role's folder against its row of catalog/role-contracts.yaml: prompt, schema, charter pin, tools; each call's inputs; each file written
src/perfrepair/check/device.py : device-level files: manifest.yaml, primitives_missing.yaml and benchmark_coverage.yaml, measurements and run log beside rows (a malformed file is its problem), primitives.tsv against rows, measurements and screen.json, bundled-suggestions.yaml, used.json against items.json, each outbox's charter.json rehashed to its folder name, events.jsonl
src/perfrepair/check/grouping.py : grouping files: the outbox and knowledge rebuilt by their kind, supervisor.json against the review outbox's replay and the current groups, screen.json against the resolved catalog; the classify outbox, classified.json, model verdicts and registry-candidates.yaml when screen.json was reviewed; each worthiness-<perfMode> folder under its own perfMode
src/perfrepair/check/run.py : stage replay: validate every artifact present in a device folder, each by its validator
src/perfrepair/validation/__main__.py : command: validate a device folder by the resolved screening catalog (`--perfrepair-config`); exit 1 on any problem, 2 on bad usage or a missing catalog
src/perfrepair/validation/answer_text.py : text rules answer schemas share: not blank, empty or a pattern, alias patterns
src/perfrepair/validation/app.py : app.json and scopes.json: shape, contract values, recomputed scope ids and patterns; scope_problems shared with dossiers
src/perfrepair/validation/benchmark_coverage.py : log/details/benchmark_coverage.yaml: schema, run, point, item statuses, each gap a known class with its action and a reason
src/perfrepair/validation/boundary.py : one algorithm keeps one identity across results, rows, measurements, items, the used set and the catalogs
src/perfrepair/validation/bundled.py : bundled-suggestions.yaml: counts equal the lists, a matched row's entry at its pinned version, a blocked or unmatched row has a reason and no entry, only apply applies
src/perfrepair/validation/catalogue_entry.py : a catalogue entry's static checks: form, family against engine type, one id across the catalogues, one group
src/perfrepair/validation/classified.py : classify/classified.json: answers only for batched ids, ids in one batch, allowed values, a reason each
src/perfrepair/validation/dossiers/against_run.py : validate_dossiers: dossiers.json against scopes.json, groups.json and the screen verdicts: every scope once, options from the current item's group with groups.json's interop status, the app's screen status, never lowering the status
src/perfrepair/validation/dossiers/document.py : dossiers.json header with its perfMode, noOptions codes, notOffered candidates rejected or above maxChange
src/perfrepair/validation/dossiers/dossier.py : check_dossier: one dossier on its own: scope, qualified items, aliases R1..Rn, interop labels in PAIR_STATUSES (never fail), estimates of selected metrics only, change classes within maxChange, review facts
src/perfrepair/validation/dossiers/parse.py : parse_dossiers: units with their Dossiers and noOptions for the replace stage, by the same checks
src/perfrepair/validation/dossiers/units.py : dossiers.json against units.json: every unit with a member with options asked, with its stays and pairs; `provider_held_key` exactly where a member's key contract is provider-held
src/perfrepair/validation/evaluate/worthiness.py : gate C of worthiness: a reply against its group's evidence, in aliases M1..Mn; pairs must improve under the mode
src/perfrepair/validation/events.py : log/events.jsonl through read_jsonl: every whole line JSON (a cut one skipped), schema 1, every field with its type, a known kind; a partial last line
src/perfrepair/validation/failure.py : ValidationFailed, code artifact_invalid, and require: the stage gate
src/perfrepair/validation/finding.py : the one invariant finding: id, severity (blocking, advisory, undecided), subject, evidence, fix; blocking, counts
src/perfrepair/validation/grouping/code_groups.py : code-made and catalog groups equal the ones screen.json and the catalog imply; no identified item in another group
src/perfrepair/validation/grouping/interop.py : interop plan against groups, results against the plan, groups.json section, dossier options
src/perfrepair/validation/grouping/invariants.py : grouping invariants: key contract (a screened-out group no dossier offers exempt), signature, no runnable member no options, interop not run, algorithm split, stability against another run
src/perfrepair/validation/grouping/items.py : items.json and profiles.json
src/perfrepair/validation/grouping/knowledge.py : knowledge: well-formed groups, members in one group of their family
src/perfrepair/validation/grouping/output.py : groups.json (schema 3): one group or dropped per item, consistent index, `screen` equal to screen.json, code-made groups; read_groups reads it gated
src/perfrepair/validation/invariants/__init__.py : run_invariants over a device folder; app_gate, the guide's check before replace; the app's source root; the items rows.json's fixed variant inits per call
src/perfrepair/validation/invariants/__main__.py : command: every invariant of a device folder, one line each and counts; exit 1 on a blocking one
src/perfrepair/validation/json_reply.py : any model reply: JSON, and an object
src/perfrepair/validation/manifest.py : manifest: listed files exist, a counted key has its file, unique provider names, precedence 1..n
src/perfrepair/validation/measurements.py : measurements: known rows, registry metrics only, required ones present, ordered finite summaries, positive medians and kinds as the registry says
src/perfrepair/validation/parse/algorithm_classify.py : gate C of algorithm-classify: one answer per listed id, allowed values, a reason
src/perfrepair/validation/parse/grouping_assign.py : gate C of grouping-assign: an agent answer against its item, the knowledge and the signatures; a catalog group joined, never amended; an unknown generator joins no group
src/perfrepair/validation/primitives.py : primitives.tsv: unique lines, registry metric columns, screen statuses, each metric's n, and equal line for line to what rows, measurements and screen.json make
src/perfrepair/validation/primitives_missing.py : log/details/primitives_missing.yaml: schema, run, each row a known reason and action, its lists, a next step
src/perfrepair/validation/repair.py : edits.json and harness.yaml: shape, reason codes, applied scopes only; EDIT_REASONS; `valid_inputs`, also used by the report check
src/perfrepair/validation/replacements.py : replacements: known scopes, a static keep with its code per noOptions scope, edits exactly the option's provider and pins, risks the scope and option imply; consistent_units
src/perfrepair/validation/report.py : report.json: statuses, rows, funnel recount, each row's pattern, measuredBy, truth checks and categoryMismatch recomputed, recommendations above maxChange; schema_version_problems, shared with summary.json
src/perfrepair/validation/report_metrics.py : a report row's metric rows: no number without a measurement, selected as the mode says, ratio, level, noise and change by the rule, the time row's views
src/perfrepair/validation/review/grouping_review.py : gate C of grouping-review: KINDS, whose order feeds the review schema and its fingerprint; supervisor findings name only that family, arity per kind
src/perfrepair/validation/rows.py : rows: unique ids, identity present, positive sizes, a known variant
src/perfrepair/validation/run_log.py : run log: measured rows exist, every other entry has a reason
src/perfrepair/validation/scoping/__init__.py : docstring only
src/perfrepair/validation/scoping/accuracy.py : known-answer accuracy of the scoper: per pattern rule and link kind, the right readings and the wrong ones
src/perfrepair/validation/scoping/invariants.py : scoping invariants against the source: the call on its line, held_in_field setup once (a re-init accepted where the fixed variant inits per call), created_per_call in one function, inverse link sides
src/perfrepair/validation/scoping/source.py : Sources: an app's files as Code read once; line spans, the function around a line, the calls a line holds
src/perfrepair/validation/screen.py : screen.json: built from this run's items.json and profiles.json (`built` digests), its catalog identity `{source, sha256}`, one verdict per item id, statuses in the set, a source for every status but unknown, a canonical name for a never-target one, a model source for unverified, and a model source only as `model:<review fingerprint>`; validate_model_verdicts: model-sourced verdicts equal the classify answers; read_checked_screen: the gated reader assign and read_groups use
src/perfrepair/validation/suggest/site_edits.py : a member's edits against its chosen option: each kind once, the field it fills with the option's value, the kinds the option requires (`takes`, `required_kinds`, also used by the replacements check)
src/perfrepair/validation/suggest/site_inverse.py : an inverse pair the swap leaves on two items: refused on another output or a failed interop, else unverified_interop declared
src/perfrepair/validation/suggest/site_performance.py : the replacement gate's performance part: a listed perfMode's strict rule, generic's named deciding metrics and accepted losses over the code labels; recommend's change line and needs; concerns' length
src/perfrepair/validation/suggest/site_replace.py : gate C of site-replace: a reply against its unit, member by member in their aliases; the members with options all replaced or all kept, none that stays named; refuses an option with unknown pins, and a replace that changes the output while its own risks say the output leaves; risks from scope and option
src/perfrepair/validation/summary.py : summary.json against the reports: apps and funnels, modes, pattern counts, app partition per pattern
src/perfrepair/validation/units.py : units.json: every scope in one unit, ids recomputed, members connected, each cited line in that side's lifecycle
src/perfrepair/validation/upgrade.py : gate C of repair-upgrade: an offered alias and a reason, resolved to the item; upgrades.json rows against their items, none on an item not accepted
src/perfrepair/validation/used.py : used.json: each item a device item named once, a known via, apps it lists, matched within sites, deviceItems equal to items.json
src/perfrepair/validation/verdicts.py : verdicts: known groups, static equal triage, pairs are members
```
