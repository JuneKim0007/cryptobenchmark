# Settings

## Files

| file | tracked | holds |
|---|---|---|
| `perfrepair.yaml` | no | the settings below; template `perfrepair.example.yaml` |
| `.env` | no | `PERFREPAIR_AGENT`, `PERFREPAIR_MODEL`, `PERFREPAIR_EFFORT`, `ANTHROPIC_API_KEY`; template `.env.example` |

- Settings file lookup: `--perfrepair-config FILE`, then `$PERFREPAIR_CONFIG`, then `perf-repair/perfrepair.yaml`; never the working directory.
- A file named by the flag or `PERFREPAIR_CONFIG` that does not exist exits 2 with `missing_file`.
- Relative paths in the file resolve against the file's folder.
- `.env` keys outside `PERFREPAIR_*` fill unset environment keys; its `PERFREPAIR_*` keys are a layer below `perfrepair.yaml`.
- `PERFREPAIR_CONFIG` is read from the environment only, never from `.env`.

## Precedence

| layer | agent keys, per role | other keys |
|---|---|---|
| 1 | CLI flag | CLI flag |
| 2 | the role's section in `perfrepair.yaml` | `perfrepair.yaml` |
| 3 | `PERFREPAIR_*` in the environment | code default |
| 4 | `agent.*` in `perfrepair.yaml` | |
| 5 | `PERFREPAIR_*` in `.env` | |
| 6 | the role's code default | |
| 7 | the general code default | |

- `agent.effort` or `PERFREPAIR_EFFORT` sets every role, assign included; `--effort` or the role's own `effort` sets one role.
- Effort stays out of the charter fingerprint: changing it never rotates an outbox.
- Each resolved value records its source: `cli`, `env <VAR>`, `file <path> [section]`, `.env <VAR>`, `default [role]`; each is logged once at INFO on stderr: `setting <key>: <value> (<source>)` (`config/load.py`).

## Keys

| key | values | default | used by |
|---|---|---|---|
| `agent.backend` | `claude-code`, `claude`, `dry-run` | `claude-code` | `--agent` of every model-calling command |
| `agent.model` | a model id | `claude-opus-5-5` | `--model` |
| `agent.effort` | `low`, `medium`, `high`, `xhigh`, `max` | `medium` | `--effort` |
| `agent.claudeBinary` | a command | `claude` | the `claude-code` backend's CLI |
| `paths.run` | a folder | none | `--run` of `grouping assign`, `grouping report`, `ai`, `guide` |
| `paths.results` | a folder | none | `--results` of `guide` |
| `paths.prompts` | a folder | packaged prompts | `--prompts` |
| `grouping.turns`, `grouping.sessions` | positive integers | 3, 2 | `grouping assign` |
| `grouping.limit` | a positive integer | all items | `grouping assign --limit` |
| `guide.mode` | `latency`, `battery` | `latency` | `guide --mode` |
| `guide.limit` | a positive integer | all scopes | `guide --limit` |
| `guide.device` | `true`, `false` | `false` | `guide --device` |
| `guide.config` | a `global.yaml` | `pipeline.py`'s lookup | `guide --config` |
| `screening.catalog` | a file | the packaged `catalog/screening.yaml`, logged | `grouping build`, `repair dossier`, `guide`, `validation` ([screening.md](screening.md) Settings) |
| `screening.aiReview` | `true`, `false` | `false` | `grouping build`: the model review of unknown items |

| role | file section | role default |
|---|---|---|
| `grouping assign` | `grouping.assign` | effort `low` |
| `grouping report --supervisor` | `grouping.supervisor` | none |
| `guide` | `guide.agent` | none |
| `ai worthiness` | `ai.worthiness` | none |
| `ai replace` | `ai.replace` | none |
| `grouping build` classify (with `screening.aiReview`) | `screening.classify` | none |

- A role section takes the agent keys: `backend`, `model`, `effort`, `claudeBinary`.

## Errors

| code | when |
|---|---|
| `unknown_keys: <path> [...], known [...]` | a key the section does not define |
| `invalid: <path> <value>, <expected>` | a value outside its set or type; env values name the variable |
| `secret_key: <path>` | a key that names an API key, token, secret or password, or a value shaped like an Anthropic key |
| `invalid_yaml: <file>` | the file is not YAML |
| `missing_file: <file> (<origin>)` | the flag or `PERFREPAIR_CONFIG` names no file |

- Every error exits 2 through the command's argument parser; an error from the file ends with ` (<file>)`.

## Inputs

An input with a fallback is resolved by `inputs/resolve.py` from its row in `inputs/table.py`: a chain of candidates (flag, environment, setting, packaged default) and a `Need`.

| Case | Result |
|---|---|
| a value set explicitly (flag, environment, setting) loads | used; not logged |
| a value set explicitly does not load | error `missing_file: <input>: <value> (<source>)`; never a fallback |
| unset | the next candidate |
| the packaged default loads | used; one log line `<input>: <source> <note>`, code `default` |
| nothing found, `REQUIRED` or `DEFAULT` | error `missing_input` |
| nothing found, `OPTIONAL` | the null value; one log line, code `not_found` |

- Log records go through the standard `logging` module (logger `perfrepair.inputs`) with `extra` `code`, `input`, `source`; each command's `__main__` attaches one stderr handler (`log.py`), nothing does at import.
- Rows: `screening.catalog` ([screening.md](screening.md)).

## Backend environment

- A `claude-code` CLI that cannot be started or answers with an error is `claude_cli_failed`, one error line from the command.
- The `claude-code` backend runs its CLI without `ANTHROPIC_API_KEY` or `ANTHROPIC_AUTH_TOKEN` in the child environment; it uses the CLI's logged-in subscription.
- The `claude` backend reads `ANTHROPIC_API_KEY` from the environment or `.env`.
