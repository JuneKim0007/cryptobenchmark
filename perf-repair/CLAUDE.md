# perf-repair

## Route
- code style for any code: naming, comments, generality → `agents/code.md`
- dto, files, run directory, benchmark in/out: manifest, results, run log, app sites → `agents/data.md`
- grouping primitives into interchangeable groups: families, items, gates, supervisor → `agents/grouping.md`
- model decisions: decision kinds, prompts, agents, the engine loop, retry → `agents/decisions.md`
- static tools: evidence, modes, triage → `agents/static-tools.md`
- repair: app call sites, replacements, patches, before/after → `agents/repair.md`
- validation: artifact validators, outbox projection, the stage gate → `agents/validation.md`
- docs, guides and file maps: writing or changing any .md → `../agents/docs/writing.md`
- facts: pipeline, artifacts, decisions, grouping, modes, repair, limits → `docs/index.md`

## Rules
- principle: the model only decides; every number, list, filter and check is a static tool.
- generality: code names no device, provider, algorithm or engine type; tests and fixtures may.
- dependency: `dto` imports nothing ← `files`, `run_dir` ← `data_handler`, `result` ← `ai/runtime` (agent, engine, prompt) ← `validation` ← `ai/evaluate`, `ai/parse`, `ai/review`, `grouping`, `repair`.
- change: one file, one responsibility; update the owning map in the same change.
- delete/rename: grep the symbol or path, remove its references first, re-grep returns nothing.
- check: `make check` green before a change is done.
- entry: `CLAUDE.md` is a byte copy of `AGENTS.md`; edit `AGENTS.md`, then `cp AGENTS.md CLAUDE.md`.
- docs: kebab-case `.md` names; root standards (`AGENTS.md`, `README.md`, `CLAUDE.md`) stay UPPER.
- commit: never `.env` or `runs/`.

## Workflow
- guide change: edit `AGENTS.md` → `cp AGENTS.md CLAUDE.md` → `make docs-lint`
- code change: owning map line → `make check`

## File structure

```
.env.example : template for `.env`: PERFREPAIR_AGENT, PERFREPAIR_MODEL, PERFREPAIR_EFFORT, ANTHROPIC_API_KEY
.gitignore : local state kept out of git: caches, `runs/`, `.venv/`, `.env`
AGENTS.md : agent entry: route, rules, file map
CLAUDE.md : byte copy of AGENTS.md
Makefile : test, docs-lint, check
README.md : what perf-repair is, setup
agents/ : guides: directives per component
docs/ : facts; map in docs/index.md
pyproject.toml : package, pyyaml dependency, optional `test` and `api` extras, pytest settings
src/perfrepair/ : the perfrepair package; each module is mapped in the guide its route names
src/perfrepair/refeed/__init__.py : refeed package; holds no code
tests/ : pytest suites, one per module or stage; `helpers.py` shared builders
tests/fixtures/ : recorded benchmark results, a demo app tree, a fake pipeline.py
tests/grouping/ : grouping stage suites; `conftest.py` and `grouping_data.py` shared data
```
