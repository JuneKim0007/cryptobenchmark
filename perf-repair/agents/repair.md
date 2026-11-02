# Repair

## Calls
- `docs/repair.md` : steps, inputs, outputs, limits
- `docs/replacement.md` : the flow from scope to measured before/after

## Rules
- scope: the model's choice is the worthiness verdict's pair; everything here is a static join, rewrite or report.
- edit: apply by exact span only; a span that cannot be re-found or read is a coded rejection, never a guess.
- edit: never write inside the app root; copies go to `<app>/original/` and `patched/`.
- edit: a splice keeps the file's line count; harness extraction relies on it.
- edit: never edit a constant's declaration or render code from model text; constants come from `specs.yaml`.
- edit: a new reason code goes in `EDIT_REASONS` (`validation/repair.py`) and the limits table of `docs/repair.md`.
- pin: a new parameter spec is a row in `specs.yaml`, never code.
- order: scope → dossier → test-set (per-app benchmark run) → replace → edit → harness → device → report.
- guide: `guide/steps.py` chains the stage functions and commands; it adds no logic of its own and stops at the first failing step with a coded reason.
- report: never invent a number; a metric without both runs is `not measured` with the first step that stopped it.

## File structure

```
src/perfrepair/__main__.py : command: `python3 -m perfrepair guide`; dispatch only
src/perfrepair/failure.py : FAILURES and reported: every command's failure as one `error ...` line and exit 1; the guide's step failures
src/perfrepair/guide/command.py : guide arguments, the step loop, one status line per step, the dry-run ending
src/perfrepair/guide/steps.py : Guide settings and the steps: prerequisites, app, dossier, replace, edit, harness, device, report; Stop codes
src/perfrepair/repair/__main__.py : command: dossier | test-set | edit | harness, each `--device-results --app`; `--perfrepair-config` fills the folder and the screening catalog
src/perfrepair/repair/dependencies.py : identifiers a function uses but does not define, from tokens
src/perfrepair/repair/dossier.py : command step: scopes + groups + measurements + the given screening Catalog (refused unless screen.json recorded it) at app.json's targetSdk → <app>/dossiers.json, validated before writing
src/perfrepair/repair/edit/__init__.py : re-exports edit_app, load_specs and the source helpers harness reads: read_source, language, function_lines, import_lines
src/perfrepair/repair/edit/algorithm.py : set_algorithm: the literal algorithm argument rewritten
src/perfrepair/repair/edit/app.py : an app's replace decisions applied to copies; edits.json document
src/perfrepair/repair/edit/init.py : the one init call on the engine a scope's call returns
src/perfrepair/repair/edit/lines.py : whole lines of a source: a function's line range, its import lines
src/perfrepair/repair/edit/literal.py : a string rendered as a Java or Kotlin literal
src/perfrepair/repair/edit/locate.py : a scope's function span and its call re-found with the scope step's lexer; argument spans or a coded rejection
src/perfrepair/repair/edit/parameters.py : pin_parameters: the init's parameter spec rendered or its pinned fields overridden
src/perfrepair/repair/edit/plan.py : one scope's edits turned into splices through the kind → apply function table, or a coded rejection
src/perfrepair/repair/edit/provider.py : set_provider: the provider argument rewritten or appended
src/perfrepair/repair/edit/reject.py : the coded rejection an edit raises
src/perfrepair/repair/edit/specs.py : specs.yaml loaded: spec choice by pinned fields, field rendering
src/perfrepair/repair/edit/specs.yaml : JCA parameter specs: constructor arguments, field types, defaults, render templates
src/perfrepair/repair/edit/splice.py : exact-span replacement that keeps line numbers; unified diff
src/perfrepair/repair/harness.py : harness.yaml: each applied scope's original and patched function, imports, inputs, current and option item, dependencies
src/perfrepair/repair/inputs.py : a scope's harness inputs: the app's static sizes, else the run's effective.yaml sizes both items share; their source
src/perfrepair/repair/names.yaml : keywords, primitive types and implicit names per language
src/perfrepair/repair/test_set.py : dossiers.json → cryptobenchmark test set: each scope's current item and every option
src/perfrepair/report/__main__.py : command: `app --device-results --app [--mode]` | `summary --device-results`
src/perfrepair/report/app_report.py : an app's step files → report.json: a row per scope, the funnel
src/perfrepair/report/command.py : stage: report.json and .md, summary.json and .md, validated before writing
src/perfrepair/report/markdown.py : report.md and summary.md from their documents
src/perfrepair/report/measured.py : cryptobenchmark's scoped-plan.yaml and scoped benchmark.json for one app; refuses a plan of another harness
src/perfrepair/report/metrics.py : before and after cases → per metric: medians, ratio, pImprove, level; ops/s and MB/s
src/perfrepair/report/scope_row.py : one scope's decision, edit, compile, interop, metrics and verdict
src/perfrepair/report/summary.py : report.json files → summary.json: funnel sums, apps improved, unchanged, worse per metric
```
