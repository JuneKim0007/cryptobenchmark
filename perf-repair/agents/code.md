# Code

## Rules
- python: 3.10+, stdlib and pyyaml only; the anthropic SDK only in `orchestrate/agent/claude.py`.
- shape: dataclasses for data; a module holds one responsibility; `__init__.py` only re-exports.
- names: snake_case modules named for their one job; a stage command is named for its stage.
- generality: engine types, aliases and precedence come from the probe and manifest, never from literals.
- files: every artifact is read and written through `files.py` and named in `run_dir.py`.
- tests: one test file per module or stage; fixtures use fake names except recorded benchmark data.

## Comments
- Comment why, not what: a constraint, a measurement, a rejected alternative, a trap.
- A module docstring states its one responsibility when the file name does not.
- No author, date, ticket or changelog comments.
- A change updates or deletes every comment it made untrue.
