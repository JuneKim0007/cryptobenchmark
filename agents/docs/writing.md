# Writing docs

## Rules
- role: guides (`AGENTS.md`, `agents/`) hold directives; docs (`docs/`) hold facts.
- ownership: one fact, one owner; grep for it before writing; elsewhere link.
- edges: guides → docs → docs; never docs → guides.
- guide content: directives only; never restate what the code or the layout shows.
- doc content: facts and invariants; a doc never decides.
- reasoning: no `because`/`so` clauses, alternatives or history in guides or docs; the why goes in a code comment.
- form: one statement per fact; a table when facts share attributes; no prose a table or bullet can carry.
- conflict: code is the source; a doc that disagrees with it is corrected.
- enforced by `make docs-lint`.

## Templates
- entry (`AGENTS.md`): `## Route` · `## Rules` · `## Workflow` · `## File structure`
- component guide: `## Calls` · `## Rules` · `## Workflow` · `## File structure`; omit empty sections
- map: flat `path : responsibility` lines, sorted by path, one code block
- index (`index.md` in every docs folder): title + one map
- fact doc: facts and invariants only; a pipeline doc starts with `## Diagram` (Mermaid)

## File structure

```
scripts/docs_lint.py : fails on CLAUDE.md ≠ AGENTS.md, missing or doubly mapped paths, unsorted maps, unmapped source files, docs folders without index.md, unreachable .md, docs → guides links
```
