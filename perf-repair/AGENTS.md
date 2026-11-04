# perf-repair

## Route
- code style for any code: naming, comments, generality → `agents/code.md`
- dto, files, device folder, benchmark in/out: manifest, results, run log, app sites → `agents/data.md`
- grouping primitives into interchangeable groups: families, items, gates, supervisor → `agents/grouping.md`
- model decisions: decision kinds, prompts, agents, settings (`perfrepair.yaml`, `.env`), the engine loop, retry → `agents/decisions.md`
- static tools: evidence, modes, triage → `agents/static-tools.md`
- app source: detect call sites, libraries, scopes (function, sinks, key source) → `agents/app.md`
- repair: app call sites, replacements, edits, harness, before/after → `agents/repair.md`
- validation: artifact validators, outbox projection, the stage gate, stage replay (`check/`) → `agents/validation.md`
- docs, guides and file maps: writing or changing any .md → `../agents/docs/writing.md`
- facts: pipeline, artifacts, decisions, grouping, modes, repair, settings, limits → `docs/index.md`

## Rules
- principle: the model only decides; every number, list, filter and check is a static tool.
- generality: code names no device, provider, algorithm or engine type; tests and fixtures may.
- dependency: each layer imports only from the layers before it, and no packages import each other in a cycle (each `__main__` is its own node); `tests/test_layers.py` checks it: `dto`, `catalog` ← `files`, `run_dir`, `inputs`, `log`, `stop`, `child` ← `config` ← `data_handler` ← `result` ← `app`/`scope`/`screen`/`source` (static) ← `validation` (validators only) ← `ai/runtime` ← model roles ← stages (`grouping`, `repair`, role commands) ← `device` ← `report`, `failure` ← `guide`, `check` ← every `__main__`.
- change: one file, one responsibility; update the owning map in the same change.
- delete/rename: grep the symbol or path, remove its references first, re-grep returns nothing.
- check: `make check` green before a change is done.
- docs: kebab-case `.md` names; root standards (`AGENTS.md`, `README.md`) stay UPPER.
- commit: never `.env`, `perfrepair.yaml`, `targets.yaml` or `runs/`.

## Workflow
- guide change: edit `AGENTS.md` → `make docs-lint`
- code change: owning map line → `make check`

## File structure

```
.env.example : template for `.env`: PERFREPAIR_AGENT, PERFREPAIR_AUTH, PERFREPAIR_MODEL, PERFREPAIR_EFFORT, ANTHROPIC_API_KEY
.gitignore : local state kept out of git: caches, `runs/`, `.venv/`, `.env`, `perfrepair.yaml`, `targets.yaml`
AGENTS.md : agent entry: route, rules, file map
Makefile : test, docs-lint, check; coverage-guide, the guide under coverage and the functions no run entered
README.md : what perf-repair is, setup
agents/ : guides: directives per component
docs/ : facts; map in docs/index.md
perfrepair.example.yaml : template for `perfrepair.yaml`: aiGateway, paths.prompts, device, apps
pyproject.toml : package, pyyaml dependency, optional `test`, `api` and pinned `scope` extras, pytest settings
src/perfrepair/ : the perfrepair package; each module is mapped in the guide its route names
targets.example.yaml : template for an apps.targets file: a root entry and a path entry
tests/ : pytest suites, one per module or stage; `helpers.py` shared builders; `conftest.py` isolates every test from local settings
tests/fixtures/ : recorded benchmark results, a demo app tree, a fake pipeline.py; `lifecycle/` own-written Java and Kotlin sources, one site per binding kind and status; `units/` own-written sources, one class per kind of link; `invariants/emu-api30/grouping/` an API 30 emulator run's groups.json, profiles.json, checks.json and screen.json trimmed to the generator groups and one digest group; `runtimes/<runtime>/` probe and trial of JDK 17, 21, 25 and Android API 36, trimmed to what grouping build and screening read
tests/grouping/ : grouping stage suites; `conftest.py` and `grouping_data.py` shared data
tools/unrun.py : the functions a coverage data file shows no run entered, one `<file>:<line> <name>` line each; needs `coverage`
```
