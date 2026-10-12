# Grouping

## Calls
- `docs/grouping.md` : contracts, files, gates, retry policy, families
- `agents/decisions.md` : agents and conversations the loop uses
- `agents/validation.md` : the validators the gates run

## Rules
- tiers: a family is static (catalog, engine type + key kind); a group is an agent's decision inside one family; key size, tag length, key residency and availability are static capabilities, never group identity.
- items: ids `1..n` per run; `items.json` is never edited after build; the agent sees `{id, type, name, provider, resolved}` and its family's groups only.
- commit: the outbox record is the commit; knowledge, cursor and errors are projections rebuilt from it; nothing writes knowledge directly.
- gates: A before every pop, B after it, C on every answer, D after every write; a failed gate stops the stage.
- retry: a rejected answer goes back to the same conversation with the problems (`--turns`); then a fresh conversation (`--sessions`); then the item is dropped.
- families: a new family is a catalog entry, not code; descriptions in the catalog are immutable to agents.
- supervisor: findings only; it never edits a group.
- checks: a static finding is one function in `grouping/report/rules.py`.

## Workflow
- run: `build` → `assign` → `report [--supervisor]` (`python3 -m perfrepair.grouping`)
- add a static check: function in `rules.py` → `RULES` → row in `docs/grouping.md`
- change the answer contract: `prompt/schema.py` → `prompt/assign.system.md` → `validation/grouping/answer.py` → `docs/grouping.md`

## File structure

```
src/perfrepair/grouping/__main__.py : command: build | assign | report [--supervisor]
src/perfrepair/grouping/build/items.py : benchmark documents → items and profiles; ids in (family, name, provider) order
src/perfrepair/grouping/build/key_kind.py : key kind from recorded fields: measured → engine type → key generator → declared → unknown
src/perfrepair/grouping/build/stage.py : stage: manifest → items.json, profiles.json, validated before writing
src/perfrepair/grouping/catalog/families.py : the family catalog and (engine type, key kind) → family
src/perfrepair/grouping/catalog/families.yaml : predefined families with fixed descriptions
src/perfrepair/grouping/gates.py : gates A, B, D around every item
src/perfrepair/grouping/loop/attempt.py : one conversation's turns: ask, gate, re-ask with the problems
src/perfrepair/grouping/loop/run.py : the item loop: gates, conversations, respawn, drop, outbox, projections
src/perfrepair/grouping/paths.py : every file name under <run>/grouping/
src/perfrepair/grouping/prompt/assign.system.md : system prompt: interchangeability, identity vs capability, answer rules
src/perfrepair/grouping/prompt/render.py : one item's message: family, its groups, the item; the rejection message
src/perfrepair/grouping/prompt/schema.py : the answer's JSON schema
src/perfrepair/grouping/report/checks.py : stage: finished grouping → checks.json, groups.json
src/perfrepair/grouping/report/output.py : groups.json assembly
src/perfrepair/grouping/report/rules.py : static checks over a finished grouping
src/perfrepair/grouping/state/cursor.py : next undecided item, computed from the outbox
src/perfrepair/grouping/state/knowledge.py : knowledge as a projection of the outbox
src/perfrepair/grouping/state/outbox.py : atomic append, ordered read, temp-file recovery
src/perfrepair/grouping/supervise/render.py : one family's review message
src/perfrepair/grouping/supervise/run.py : supervisor: one review conversation per family → supervisor.json
src/perfrepair/grouping/supervise/schema.py : the supervisor's JSON schema
src/perfrepair/grouping/supervise/supervisor.system.md : supervisor system prompt: findings only
```
