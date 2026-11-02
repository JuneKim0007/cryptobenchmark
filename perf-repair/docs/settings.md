# Settings

## Files

| file | tracked | holds |
|---|---|---|
| `perfrepair.yaml` | no | the settings below; template `perfrepair.example.yaml` |
| `.env` | no | `PERFREPAIR_AGENT`, `PERFREPAIR_AUTH`, `PERFREPAIR_MODEL`, `PERFREPAIR_EFFORT`, `ANTHROPIC_API_KEY`; template `.env.example` |

- Settings file lookup: `--perfrepair-config FILE`, then `$PERFREPAIR_CONFIG`, then `perf-repair/perfrepair.yaml`; never the working directory.
- A file named by the flag or `PERFREPAIR_CONFIG` that does not exist exits 2 with `missing_file`.
- Relative paths in the file resolve against the file's folder.
- `.env` keys outside `PERFREPAIR_*` fill unset environment keys; its `PERFREPAIR_*` keys are a layer below `perfrepair.yaml`.
- `PERFREPAIR_CONFIG` is read from the environment only, never from `.env`.

## Precedence

| layer | gateway keys, per role | other keys |
|---|---|---|
| 1 | CLI flag | CLI flag |
| 2 | the role's section in `perfrepair.yaml` | `perfrepair.yaml` |
| 3 | `PERFREPAIR_*` in the environment | code default |
| 4 | `aiGateway.use`, or the gateway's block `aiGateway.<name>`, in `perfrepair.yaml` | |
| 5 | `PERFREPAIR_*` in `.env` | |
| 6 | the role's code default | |
| 7 | the general code default | |

- `aiGateway.<name>.effort` or `PERFREPAIR_EFFORT` sets every role, assign included; `--effort` or the role's own `effort` sets one role.
- `--agent`, `PERFREPAIR_AGENT` and `aiGateway.use` name the gateway; a role's `gateway` overrides them for that role.
- Gateway, model and effort stay out of the charter fingerprint: changing them never rotates an outbox.
- Each resolved value records its source: `cli`, `env <VAR>`, `file <path> [section]`, `.env <VAR>`, `default [role]`; each is logged once as `setting <key>: <value> (<source>)` (`config/load.py`): at INFO, so on stderr, when a file or the environment chose it; at DEBUG when it is a flag or a default, kept for the run log (#71).

## Keys

| key | values | default | used by |
|---|---|---|---|
| `aiGateway.use` | a registered gateway: `claude`, `dry-run` | `claude` | `--agent` of every model-calling command; `PERFREPAIR_AGENT` |
| `aiGateway.claude.auth` | `subscription` (the logged-in CLI), `api` (`ANTHROPIC_API_KEY`) | `subscription` | `--auth`; `PERFREPAIR_AUTH` |
| `aiGateway.claude.model` | a model id | `claude-opus-5-5` | `--model`; `PERFREPAIR_MODEL` |
| `aiGateway.claude.effort` | `low`, `medium`, `high`, `xhigh`, `max` | `medium` | `--effort`; `PERFREPAIR_EFFORT` |
| `aiGateway.claude.binary` | a command | `claude` | the CLI of `auth: subscription` |
| `paths.run` | a folder | none | `--run` of every `grouping` step, `ai`, `guide`: one run directory for the whole chain, and a rebuild beside later stages fails their `built` digests instead of passing silently |
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

- A role section takes the keys `gateway`, `model`, `effort`.
- `auth` and `binary` belong to the gateway's block; a role section refuses them.
- The `dry-run` gateway has no keys and ignores `--auth`, `--model`, `--effort`; each role answers with its own stand-in.

## Errors

| code | when |
|---|---|
| `unknown_keys: <path> [...], known [...]` | a key the section does not define, `agent`, `backend` and `claudeBinary` included |
| `unknown_gateway: <name> (<where>), known [...]` | a name or a block under `aiGateway` no registered gateway owns |
| `missing_secret: <VAR>: gateway <name> ...` | the gateway's secret is in neither the environment nor `.env` |
| `invalid: <path> <value>, <expected>` | a value outside its set or type; env values name the variable |
| `secret_key: <path>` | a key that names an API key, token, secret or password, or a value shaped like an Anthropic key |
| `invalid_yaml: <file>` | the file is not YAML |
| `missing_file: <file> (<origin>)` | the flag or `PERFREPAIR_CONFIG` names no file |

- The file's sections other than the gateway blocks are checked at load: an error exits 2 through the command's argument parser and ends with ` (<file>)`.
- A gateway's block is checked at spawn, against that gateway's settings class, every block on each spawn; `unknown_gateway`, `missing_secret` and the block's `unknown_keys` and `invalid` print one `error ...` line and exit 1 before the command does any work.
- An `invalid` from a resolved value names the role's key and ends with the value's source: `invalid: grouping.assign.effort hgh, one of [...] (env PERFREPAIR_EFFORT)`.
- A command that calls no model reads no gateway block.

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

## Gateways

```yaml
aiGateway:
  use: claude
  claude:
    auth: subscription
    model: claude-opus-5-5
    effort: medium
    binary: claude
grouping:
  assign: {effort: low}
```

| gateway | keys | secret | reaches |
|---|---|---|---|
| `claude`, `auth: subscription` | `auth`, `model`, `effort`, `binary` | none | the logged-in `claude` CLI |
| `claude`, `auth: api` | `auth`, `model`, `effort` | `ANTHROPIC_API_KEY` | the Messages API; needs `pip install -e .[api]` |
| `dry-run` | none | none | no model |

- `--agent claude` names the gateway, and without `auth` it runs the logged-in CLI, never the API key: billing follows `auth`, and only `auth: api` or `--auth api` reaches the Messages API.
- `claude-code` is no gateway name: `--agent claude-code` is a usage error and `PERFREPAIR_AGENT=claude-code` is `unknown_gateway`.
- A CLI that cannot be started or answers with an error is `claude_cli_failed`, one error line from the command.
- `auth: subscription` runs its CLI without `ANTHROPIC_API_KEY` or `ANTHROPIC_AUTH_TOKEN` in the child environment.
- `auth: api` without the `anthropic` package is `claude_api_missing`.
- A secret in `perfrepair.yaml` is `secret_key`, in any block, a block no gateway owns included.
- Each outbox record holds the `gateway`, `model` and `effort` that answered it; a resume whose values differ from earlier records logs one `mixed_agents` line naming both (`docs/decisions.md`).
