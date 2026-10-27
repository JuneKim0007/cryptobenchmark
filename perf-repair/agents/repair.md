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
- order: candidates → test-set → (benchmark run, grouping, worthiness) → choose; scope → replace → edit → harness → replay.

## File structure

```
src/perfrepair/repair/__main__.py : command: candidates | test-set | choose | edit | harness | replay
src/perfrepair/repair/candidates.py : sites.json × groups.json → each site's item and its group's runnable alternatives
src/perfrepair/repair/choose.py : worthiness verdicts × candidates → the replacement per site, or none with the verdict's reason
src/perfrepair/repair/dependencies.py : identifiers a function uses but does not define, from tokens
src/perfrepair/repair/edit/__init__.py : re-exports edit_app
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
src/perfrepair/repair/paths.py : the files of one app under <run>/apps/<app>/
src/perfrepair/repair/replay.py : before/after for one site from a benchmark run: mean, median, MB/s, µJ/op
src/perfrepair/repair/test_set.py : candidates → cryptobenchmark test set of the items an app runs and their alternatives
```
