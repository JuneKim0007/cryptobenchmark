# Writing docs

## Calls
- `scripts/docs_lint.py` : the checks `python3 scripts/docs_lint.py` runs

## Rules
- scope: these rules apply to every `.md` in the repo, `perf-repair/` included.
- role: guides (`AGENTS.md`, `agents/`, `perf-repair/AGENTS.md`, `perf-repair/agents/`) hold directives; docs (`docs/`, `modules/<m>/docs/`, `perf-repair/docs/`) hold facts.
- placement: a cross-module fact lives in `docs/`; a fact about one module lives in `modules/<m>/docs/`; a perf-repair fact lives in `perf-repair/docs/`.
- navigation: `AGENTS.md` `## Route` → guide → its `## Calls` or a `docs/**/index.md` → the file; every guide and doc is reachable that way.
- ownership: one fact, one owner; grep for it before writing; elsewhere link it.
- edges: guides → docs → docs; a doc never names `AGENTS.md` or a guides folder.
- links: backticked repo-relative paths or relative markdown links; inside `perf-repair/`, paths are relative to `perf-repair/`.
- guide content: directives only, one line each, `- topic: imperative`; never restate what the code or the layout shows.
- doc content: facts and invariants, stated as facts; a directive belongs in a guide.
- reasoning: no `because`, `so that`, `in order to`, `which means` or `instead of` clauses; the why goes in a code comment, the commit message or the PR body.
- history: no dates except data values, no status, plans, `next`, task or issue ids, changelogs, decision records or verification results.
- form: one fact per line; a table when facts share attributes; no paragraphs, no narration.
- examples: keep an example only when it is the contract (a YAML shape, a CLI line).
- language: English, plain words; no em dashes, no decorative bold; no sentence about the document itself.
- headings: sentence case, no numbering, named for what the section holds.
- size: at most 150 lines per guide or doc; most fit under 80.
- conflict: code is the source; a doc that disagrees with it is corrected, never followed.
- oddities: a code oddity is never written into a doc; report it in the change.
- read by code: before moving or deleting a doc, grep code, scripts, tests, workflows and Makefiles for its path; keep paths they name.
- generated: `modules/environment/discovery/docs/tree.md` is stdout of `tools/jca-contract/src/main/kotlin/examples/Tree.kt`; regenerate it, never hand-edit it.
- generated: `docs/shared-functions.md` and `perf-repair/docs/shared-functions.md` are written by `python3 scripts/shared_functions.py`; rerun it after a change to what modules import, never hand-edit them.
- generated: `perf-repair/docs/screening-list.md` is written by `python3 scripts/screening_list.py`; rerun it after a change to `screening.yaml`, never hand-edit it.
- runtime prompts: `perf-repair/src/**/*.system.md` are code; keep them out of the docs graph.
- readme: a module `README.md` is 3 to 6 lines: what the module is and a link to its `docs/index.md`.
- diagram: Mermaid code blocks inside the doc.

## Workflow
- add a doc: template → its line in the folder `index.md` (a guide: a `## Route` or `## Calls` line)
- modify: change only the stale statement; keep headings, they are link targets
- finish: `python3 scripts/docs_lint.py`

## Templates
- entry (`AGENTS.md`): `## Route` · `## Rules` · `## Workflow` · `## File structure`
- guide: `## Calls` · `## Rules` · `## Workflow` · `## File structure`; omit empty sections
- map: flat `path : responsibility` lines, sorted by path, one code block, no tree glyphs; a folder line (`dir/ : ...`) owns every file under it; a responsibility that needs "and" for two unrelated jobs marks a split
- index (`index.md` in every docs folder): title + one map
- module index (`modules/<m>/docs/index.md`): title + one map of the module's files, paths relative to the repo root, its own docs included
- fact doc: facts and invariants only; a flow doc starts with `## Diagram` (Mermaid)
