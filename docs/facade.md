# Facade

`python3 apps/cli/facade.py --settings <settings.yaml> [--check]`: one command for benchmark then guided repair.

## Settings index

Template: `settings.example.yaml`. Relative paths resolve against the file holding them. A key not below is an error.

| key | holds |
|---|---|
| `schemaVersion` | `1` |
| `results` | the results root, `<results>/<device id>/`; created when absent, its parent must exist |
| `run.id` | names `runs/run_<id>.json`; empty: a new timestamp id |
| `run.onExisting` | `overwrite`, `resume`, `skip` ([artifacts.md](../apps/perf-repair/docs/artifacts.md#run-record)) |
| `crypto.config` | the `global.yaml` of the benchmark |
| `crypto.harnessConfig` | optional: a lighter `global.yaml` for the per-app device step (compile and interop check); unset: `crypto.config` |
| `llm.config` | the `perfrepair.yaml` of the guided repair; `perfMode` stays there |

## Direction rule

```
settings.yaml -> crypto.config -> selection.testSet
              -> llm.config    -> apps.targets, device.screening.catalog, paths.prompts
every side    -> packaged catalogs
```

| refused | code |
|---|---|
| a pointer at a file another side holds | `direction: ... points sideways` |
| a pointer back at a file above it | `direction: ... points up` |
| a `perfrepair.yaml` key of the table below, with a value | `placement: <key> is no perfrepair.yaml key; set <place>` |
| a key of another file in `perfrepair.yaml` | `placement: <key> in <file> belongs in ...` |
| a key nothing reads in `perfrepair.yaml` | `unknown_key: <key> in <file>` |
| a key of another file in `global.yaml` | `config_invalid: global.yaml: unknown_section: ...` |

| `perfrepair.yaml` key refused | index key | guide flag |
|---|---|---|
| `paths.results` | `results` | `--results-root` |
| `device.benchmark.config` | `crypto.config` | `--config` |
| `apps.benchmarkConfig` | `crypto.harnessConfig` | `--harness-config` |
| `run.id` | `run.id` | `--run-id` |
| `run.onExisting` | `run.onExisting` | `--on-existing` |

## Check

Runs first on every facade run; `--check` stops after it. No app build, no device, no model.

| check | by |
|---|---|
| every path exists | `missing_file: <path> (<key> in <file>)` |
| `global.yaml` and its test set | `CheckConfigKt`: the Kotlin parsers on the JVM, compiled by Gradle on first use |
| `perfrepair.yaml` | `perfrepair.config.load` and its rows; unknown keys refused |
| targets file, screening catalog, prompts | `listed_entries` and `resolve_targets`, `load_catalog`, `PromptLibrary.load` |
| catalogs | every packaged `*.yaml` with path, digest, `packaged`; a set one `overridden` in its place |

- The tree and each file's digest are stored under `settings` in `runs/run_<id>.json` through `RunRecord`.
- `pipeline.py` runs the same parse-only step before any build, `--identify` excepted.

## Phases

| phase | command | does | line |
|---|---|---|---|
| check | in process | above | `facade check: check_ok: ...`, or its first problem |
| crypto | `guide --results-root <results> --stop-after-device` | target detect, used set, benchmark, inbound; no model call | `facade crypto: crypto_ok: device <folder>, run <id>`, `crypto_failed: <code> exit=<n>`, `crypto_not_run` |
| guided | `guide --device-results <folder> --run-id <id> --on-existing resume` | grouping, each app; no benchmark | `facade guided: guided_ok`, `guided_stopped: <code> exit=<n>`, `guided_not_run` |

- A failed phase stops the next; the exit code is the worst.
- Every child gets `--perfrepair-config` and `--config`, `PERFREPAIR_CONFIG` set to `llm.config`, `CRYPTOBENCH_CONFIG` unset and `CRYPTOBENCH_ROOT` set to this repository; the home folder's `global.yaml` and the package's default `perfrepair.yaml` are not read.
- `PERFREPAIR_AGENT` and the other gateway variables keep their layer ([settings.md](../apps/perf-repair/docs/settings.md)).
- Lower-level commands: `apps/benchmark-runner/pipeline.py` ([run.md](run.md)), `python3 -m perfrepair guide` ([replacement.md](../apps/perf-repair/docs/replacement.md)). `apps/benchmark-runner/demo.sh` stays crypto only.
