# Code

## Rules
- python: 3.10+, stdlib and pyyaml only; the anthropic SDK only in `src/perfrepair/ai/runtime/agent/claude.py`.
- shape: dataclasses for data; a module holds one responsibility; `__init__.py` only re-exports or holds a docstring.
- names: snake_case modules named for their one job; a stage command is named for its stage.
- generality: engine types, aliases and precedence come from the probe and manifest, never from literals.
- commands: a `__main__` runs its work through `failure.reported`; a new failure type a command can raise joins `FAILURES`.
- files: every artifact is read and written through `files.py` and named in `run_dir.py`.
- tests: one test file per module or stage; fixtures use fake names except recorded benchmark data.
- comments: why only: a constraint, a measurement, a rejected alternative, a trap; at most two lines.
- docstrings: a module docstring states its one responsibility when the file name does not.
- comments: no author, date, ticket or changelog.
- comments: a change updates or deletes every comment it made untrue.
