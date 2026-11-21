# config

Every file a user edits, by the tool that reads it. Each tracked template is copied beside itself; the copies are git-ignored. Nothing here is generated.

| file | reader | lookup |
|---|---|---|
| `config/benchmark/global.yaml` | `apps/benchmark-runner/pipeline.py` (`lib/cryptobench/cryptobench/stages/configuration/global_file.py`) | `--config`, then `$CRYPTOBENCH_CONFIG`, then `~/.config/cryptobench/global.yaml`, then this file |
| `config/benchmark/testsets/*.yaml` | the config module | `selection.testSet` of the run's `global.yaml`, relative to it |
| `~/.config/cryptobench/global.yaml` | `apps/benchmark-runner/pipeline.py` | third in the `global.yaml` order |
| `~/.config/cryptobench/devices.yaml` | `apps/benchmark-runner/pipeline.py` `--devices`, `--session` | fixed; absent is no aliases |
| a `session.yaml` (no committed copy) | `apps/benchmark-runner/pipeline.py` `--session`, `--check-session` | the flag; its paths resolve against its folder |
| `apps/benchmark-runner/energy/requirements.txt`, `requirements-manafa.txt` | the `--energy-python` interpreter's install | fixed, beside the energy scripts; installed on first use |
| `requirements.txt` | `pip install -r`, CI | fixed, at the repository root |
| `lib/cryptobench/cryptobench/shared/settings/defaults.yaml` | the runner and perf-repair, as package data | not edited: the config module's `-Dexamples.update` run writes it |

Fields and precedence of the benchmark files: [config.md](../apps/benchmark/modules/config/docs/config.md).
