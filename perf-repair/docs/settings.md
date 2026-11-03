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
- Each resolved value records its source: `cli`, `env <VAR>`, `file <path> [section]`, `.env <VAR>`, `default [role]`; each is logged once as `setting <key>: <value> (<source>)` (`config/load.py`): at INFO, so on stderr, when a file or the environment chose it; at DEBUG when it is a flag or a default, kept only in `log/events.jsonl`.

## Keys

- Sections: `aiGateway` and `paths` are shared, `device` is once per device, `apps` is per app.
- Every key is a row in `inputs/table.py`: its chain, check, default and `OnInvalid`. A setting ships only with the code that reads it; `tests/test_settings_rows.py` fails on a row without exactly one reader and on an example key with no row.

| key | values | default | on a bad value | used by |
|---|---|---|---|---|
| `aiGateway.use` | a registered gateway: `claude`, `dry-run` | `claude` | error | `--agent` of every model-calling command; `PERFREPAIR_AGENT` |
| `aiGateway.claude.auth` | `subscription` (the logged-in CLI), `api` (`ANTHROPIC_API_KEY`) | `subscription` | error | `--auth`; `PERFREPAIR_AUTH` |
| `aiGateway.claude.model` | a model id | `claude-opus-5-5` | warning | `--model`; `PERFREPAIR_MODEL` |
| `aiGateway.claude.effort` | `low`, `medium`, `high`, `xhigh`, `max` | `medium` | warning | `--effort`; `PERFREPAIR_EFFORT` |
| `aiGateway.claude.binary` | a command | `claude` | warning | the CLI of `auth: subscription` |
| `paths.results` | the results root | none | warning | every command's device folder when `--device-results` is unset: `<root>/<device.id>`, else its only device; the guide without either calls probe_device() on the root (`docs/pipeline.md` Device stage); a rebuild beside later stages fails their `built` digests instead of passing silently |
| `paths.prompts` | a folder | packaged prompts | warning | `--prompts` |
| `device.id` | a folder under `paths.results` | its only device | error | the same; a fallback would read another device's numbers |
| `device.screening.catalog` | a file | the packaged `catalog/screening.yaml`, logged | error | `grouping build`, `repair dossier`, `guide`, `validation` ([screening.md](screening.md) Settings) |
| `device.screening.aiReview` | `true`, `false` | `false` | warning | `grouping build`: the model review of unknown items |
| `device.grouping.turns`, `device.grouping.sessions` | positive integers | 3, 2 | warning | `grouping assign` |
| `device.grouping.limit` | a positive integer | all items | warning | `grouping assign --limit` |
| `device.grouping.noRerun` | `true`, `false` | `true` | warning | the guide's grouping step (`device/coverage.py`): `true` asks only items with no decision, `false` asks every item into a new outbox, one more each run. Coverage is computed each run, so knowledge that is missing is asked under either |
| `device.benchmark.config` | a `global.yaml` | `pipeline.py`'s lookup | warning | `guide --config`: the device stage and the device step |
| `apps.targets` | a list of paths or `{path: ...}`, relative to the file | none | warning | `guide` without `--app`: every entry, in order; `--app` runs one |
| `apps.perfMode` | `generic`, or a list of `latency`, `throughput`, `memAlloc`, `energy` ([modes.md](modes.md)) | `generic` | warning | `guide --perf-mode`: the metrics the dossiers, the replace render and the report's selected marks carry, and what the device step measures |
| `apps.limit` | a positive integer | all scopes | warning | `guide --limit` |
| `apps.measure` | `true`, `false` | `false` | warning | `guide --device`; with probe_device it also makes the device stage on the phone, else on the host |

| role | file section | role default |
|---|---|---|
| `grouping build` classify (with `device.screening.aiReview`) | `device.screening.classify` | none |
| `grouping assign` | `device.grouping.assign` | effort `low` |
| `grouping report --supervisor` | `device.grouping.supervisor` | none |
| `ai worthiness` | `device.worthiness` | none |
| `guide` | `apps.agent` | none |
| `ai replace` | `apps.replace` | none |

- A role section takes the keys `gateway`, `model`, `effort`. Its `gateway` is an error when bad; `model` and `effort` warn.
- `auth` and `binary` belong to the gateway's block; in a role section they are unknown keys, warned about and never read.
- The `dry-run` gateway has no keys and ignores `--auth`, `--model`, `--effort`; each role answers with its own stand-in.

## Bad values

| value comes from | row policy | result |
|---|---|---|
| a CLI flag | any | error: the user typed it now; `--turns`, `--perf-mode`, `--agent` at argparse (exit 2), `--effort`, `--auth`, `--model` at spawn (exit 1) |
| the file, the environment or `.env` | `OnInvalid.USE_DEFAULT` | one warning, then the default; the command proceeds |
| the file, the environment or `.env` | `OnInvalid.ERROR` | error: a fallback is unsafe, it could allow broken algorithms or reach the wrong provider or account |

- The warning: `invalid: <key> <value>, <expected>; using the default <default> (<source>)`, or `; ignored (<source>)` when the row has no default.
- The default is the row's: the role's code default, then the general one; lower layers are skipped, so a bad role `effort` never picks up a dearer `PERFREPAIR_EFFORT`.
- One exception: a bad value in a gateway's block counts as unset at that layer, so a valid `.env` value below it still applies.
- A check runs when a command reads the row. A command that reads no row of a section says nothing about its values; a role's values and a gateway's block are read only by a model-calling command.
- A section that is not a mapping: an error when it holds an `OnInvalid.ERROR` row, else a warning `invalid: <section> <value>, a mapping; ignored`.

## Errors

| code | when |
|---|---|
| `unknown_gateway: <name> (<where>), known [...]` | a name or a block under `aiGateway` no registered gateway owns |
| `missing_secret: <VAR>: gateway <name> ...` | the gateway's secret is in neither the environment nor `.env` |
| `invalid: <key> <value>, <expected> (<source>)` | a bad flag, or a bad value of an `OnInvalid.ERROR` row |
| `secret_key: <path>` | a key that names an API key, token, secret or password, or a value shaped like an Anthropic key; anywhere in the file, lists and unknown keys included |
| `invalid_yaml: <file>` | the file is not YAML, so no secret check is possible |
| `missing_file: <file> (<origin>)` | the flag or `PERFREPAIR_CONFIG` names no file |
| `missing_file: <input>: <value> (<source>)` | a set `device.screening.catalog` does not load |
| `several_device_results`, `device_not_in_results`, `no_device_results`, `not_device_results` | `paths.results` does not name one device: [artifacts.md](artifacts.md#folders) |

- A key no row knows is one warning, `unknown_key: <key>, known [...] (<file>)`, a key from before the sections (`grouping`, `guide`, `ai`, `screening`) included; a block's key is checked at spawn.
- `secret_key`, `invalid_yaml` and a named file that is missing exit 2 through the command's argument parser, the first two ending with ` (<file>)`.
- A gateway's block is checked at spawn, against that gateway's settings class, every block on each spawn; errors at spawn print one `error ...` line and exit 1 before the command does any work.
- Each error and warning from a resolved value names the role's key and ends with the value's source: `invalid: device.grouping.assign.effort hgh, one of [...]; using the default low (env PERFREPAIR_EFFORT)`.

## Inputs

An input that loads a file, `device.screening.catalog`, also has a `Need` and a packaged default; `inputs/resolve.py` resolves it from its row.

| Case | Result |
|---|---|
| a value set explicitly (flag, environment, setting) loads | used; not logged |
| a value set explicitly does not load | error `missing_file: <input>: <value> (<source>)`; never a fallback |
| the packaged default loads | used; one log line `<input>: <source> <note>`, code `default` |
| nothing found | `REQUIRED`, `DEFAULT`: error `missing_input`; `OPTIONAL`: the null value, one log line, code `not_found` |

- Log records go through the standard `logging` module (logger `perfrepair.inputs`) with `extra` `code`, `input`, `source`; each command's `__main__` attaches the stderr handler and the event sink (`log/attach.py`), nothing does at import.
- `PERFREPAIR_CONFIG` and `--perfrepair-config` name the file, so they sit outside the rows.

## Gateways

```yaml
aiGateway:
  use: claude
  claude:
    auth: subscription
    model: claude-opus-5-5
    effort: medium
    binary: claude
device:
  grouping:
    assign: {effort: low}
```

| gateway | keys | secret | reaches |
|---|---|---|---|
| `claude`, `auth: subscription` | `auth`, `model`, `effort`, `binary` | none | the logged-in `claude` CLI |
| `claude`, `auth: api` | `auth`, `model`, `effort` | `ANTHROPIC_API_KEY` | the Messages API; needs `pip install -e .[api]` |
| `dry-run` | none | none | no model |

- `--agent claude` names the gateway, and without `auth` it runs the logged-in CLI, never the API key: billing follows `auth`, and only `auth: api` or `--auth api` reaches the Messages API.
- `aiGateway.use: nope` is `unknown_gateway`, one error line at spawn.
- `claude-code` is no gateway name: `--agent claude-code` is a usage error and `PERFREPAIR_AGENT=claude-code` is `unknown_gateway`.
- A CLI that cannot be started or answers with an error is `claude_cli_failed`, one error line from the command.
- `auth: subscription` runs its CLI without `ANTHROPIC_API_KEY` or `ANTHROPIC_AUTH_TOKEN` in the child environment.
- `auth: api` without the `anthropic` package is `claude_api_missing`.
- A secret in `perfrepair.yaml` is `secret_key`, in any block, a block no gateway owns included.
- Each outbox record holds the `gateway`, `model` and `effort` that answered it; a resume whose values differ from earlier records logs one `mixed_agents` line naming both (`docs/decisions.md`).
