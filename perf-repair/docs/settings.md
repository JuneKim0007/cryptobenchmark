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

| layer | agent keys | role keys | other keys |
|---|---|---|---|
| 1 | CLI flag | CLI flag | CLI flag |
| 2 | `PERFREPAIR_*` in the environment | the role's key in `perfrepair.yaml` | `perfrepair.yaml` |
| 3 | `agent.*` in `perfrepair.yaml` | the role's code default | code default |
| 4 | `PERFREPAIR_*` in `.env` | the agent keys, layers 2 to 5 | |
| 5 | code default | | |

- Role keys beat every agent layer; `PERFREPAIR_EFFORT` never lowers `grouping report --supervisor` below `high`; `--effort` or `grouping.supervisor.effort` does.
- Each resolved value records its source: `cli`, `env <VAR>`, `file <path> [section]`, `.env <VAR>`, `default [role]`.

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
| `screening.catalog` | a file | none | no command yet |
| `screening.unknown` | `model`, `unverified` | none | no command yet |

| role | file section | role default |
|---|---|---|
| `grouping assign` | `grouping.assign` | none |
| `grouping report --supervisor` | `grouping.supervisor` | effort `high` |
| `guide` | `guide.agent` | none |
| `ai worthiness` | `ai.worthiness` | none |
| `ai replace` | `ai.replace` | none |

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

## Backend environment

- The `claude-code` backend runs its CLI without `ANTHROPIC_API_KEY` in the child environment; it uses the CLI's logged-in subscription.
- The `claude` backend reads `ANTHROPIC_API_KEY` from the environment or `.env`.
