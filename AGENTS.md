# Agent

Entry point. perf-repair reads cryptobenchmark results and decides which crypto replacements are worth testing in an app. Pick the route for the task, read that file, follow its `## Rules`.

## Route
- code style for any code: naming, comments, generality → `agents/code.md`
- dto, files, run directory, benchmark in/out: manifest, results, run log, app sites → `agents/data.md`
- grouping primitives into interchangeable groups: families, items, outbox, gates, supervisor → `agents/grouping.md`
- model decisions: decision kinds, prompts, agents, the loop, stage commands → `agents/decisions.md`
- static tools: evidence, modes, triage → `agents/static-tools.md`
- validation: artifact validators, journal replay, the stage gate → `agents/validation.md`
- docs, guides and file maps: writing or changing any .md → `agents/docs/writing.md`
- facts: pipeline, artifacts, decisions, modes, limits → `docs/index.md`

## Rules
- principle: the model only decides; every number, list, filter and check is a static tool.
- generality: code names no device, provider, algorithm or engine type; tests and fixtures may.
- dependency: `dto` imports nothing ← `files`, `run_dir` ← `data_handler`, `result` ← `orchestrate` (agent, decisions, runner) ← `validation` ← `orchestrate/commands`, `grouping`.
- change: one file, one responsibility; update the owning map in the same change.
- delete/rename: grep the symbol or path, remove its references first, re-grep returns nothing.
- check: `make check` green before a change is done.
- entry: `CLAUDE.md` is a byte copy of `AGENTS.md`; edit `AGENTS.md`, then `cp AGENTS.md CLAUDE.md`.
- docs: kebab-case `.md` names; root standards (`AGENTS.md`, `README.md`, `CLAUDE.md`) stay UPPER.

## File structure

```
Makefile : test, docs-lint, check
README.md : what perf-repair is, how to run it
pyproject.toml : package, pyyaml dependency, pytest settings
src/perfrepair/refeed/__init__.py : planned layer: verdicts and failures back into the next run; empty
```
