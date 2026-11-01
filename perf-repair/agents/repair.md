# Repair

## Calls
- `docs/repair.md` : steps, inputs, outputs, limits
- `docs/replacement.md` : the flow from scope to measured before/after

## Rules
- scope: the model's choice is the worthiness verdict's pair; everything here is a static join, rewrite or report.
- edit: apply by exact span only; a span that cannot be re-found or read is a coded rejection, never a guess.
- edit: never write inside the app root; copies go to `apps/<app>/original/` and `patched/`.
- edit: a splice keeps the file's line count; harness extraction relies on it.
- edit: never edit a constant's declaration or render code from model text; constants come from `specs.yaml`.
- edit: a new reason code goes in `EDIT_REASONS` (`validation/repair.py`) and the limits table of `docs/repair.md`.
- pin: a new parameter spec is a row in `specs.yaml`, never code.
- order: scope → dossier → test-set (per-app benchmark run) → replace → edit → harness.

## File structure

```
src/perfrepair/repair/__main__.py : command: dossier | test-set | edit | harness, each `--run --app`
src/perfrepair/repair/dependencies.py : identifiers a function uses but does not define, from tokens
src/perfrepair/repair/dossier.py : command step: scopes + groups + measurements → apps/<app>/dossiers.json, validated before writing
src/perfrepair/repair/edit/__init__.py : re-exports edit_app, load_specs and the source helpers harness reads: read_source, language, lex, line_offsets
src/perfrepair/repair/edit/algorithm.py : set_algorithm: the literal algorithm argument rewritten
src/perfrepair/repair/edit/app.py : an app's replace decisions applied to copies; edits.json document
src/perfrepair/repair/edit/calls.py : a call's closing parenthesis and top-level argument spans
src/perfrepair/repair/edit/init.py : the one init call on the engine a scope's call returns
src/perfrepair/repair/edit/lexer.py : Java and Kotlin source classed as code, literal or comment; masked copy
src/perfrepair/repair/edit/literal.py : a string rendered as a Java or Kotlin literal
src/perfrepair/repair/edit/locate.py : a scope's function span and its call re-found in today's source
src/perfrepair/repair/edit/parameters.py : pin_parameters: the init's parameter spec rendered or its pinned fields overridden
src/perfrepair/repair/edit/plan.py : one scope's edits turned into splices, or a coded rejection
src/perfrepair/repair/edit/provider.py : set_provider: the provider argument rewritten or appended
src/perfrepair/repair/edit/reject.py : the coded rejection an edit raises
src/perfrepair/repair/edit/specs.py : specs.yaml loaded: spec choice by pinned fields, field rendering
src/perfrepair/repair/edit/specs.yaml : JCA parameter specs: constructor arguments, field types, defaults, render templates
src/perfrepair/repair/edit/splice.py : exact-span replacement that keeps line numbers; unified diff
src/perfrepair/repair/harness.py : harness.yaml: each applied scope's original and patched function, imports, dependencies
src/perfrepair/repair/names.yaml : keywords, primitive types and implicit names per language
src/perfrepair/repair/test_set.py : dossiers.json → cryptobenchmark test set: each scope's current item and every option
```
