# config

Every file a user edits, by the tool that reads it. Nothing here is generated.

| file | edited | reader | lookup |
|---|---|---|---|
| `config/facade/settings.yaml` | a git-ignored copy of `settings.example.yaml` beside it | `apps/cli/facade.py` | `--settings`, required; its paths resolve against its folder |
| `config/benchmark/global.yaml` | in place, tracked | `apps/benchmark-runner/pipeline.py` (`lib/cryptobench/cryptobench/stages/configuration/global_file.py`) | `--config`, then `$CRYPTOBENCH_CONFIG`, then `~/.config/cryptobench/global.yaml`, then this file |
| `config/benchmark/testsets/*.yaml` | in place, tracked | the config module | `selection.testSet` of the run's `global.yaml`, relative to it |
| `config/perf-repair/perfrepair.yaml` | a git-ignored copy of `perfrepair.example.yaml` beside it | every perf-repair command (`apps/perf-repair/src/perfrepair/config/load.py`) | `--perfrepair-config`, then `$PERFREPAIR_CONFIG`, then this file; none is code defaults, logged |
| `config/perf-repair/.env` | a git-ignored copy of `.env.example` beside it | perf-repair (`apps/perf-repair/src/perfrepair/config/dotenv.py`) | fixed; a layer below `perfrepair.yaml`; absent adds nothing |
| a targets file | a copy of `config/perf-repair/targets.example.yaml`; `config/perf-repair/targets.yaml` is git-ignored | perf-repair `apps.targets` | relative to `perfrepair.yaml`'s folder |
| a `screening.yaml` | a copy of the packaged catalog | perf-repair `device.screening.catalog` | relative to `perfrepair.yaml`'s folder; unset is the packaged catalog |
| `~/.config/cryptobench/global.yaml` | outside the repository | `apps/benchmark-runner/pipeline.py` | third in the `global.yaml` order |
| `~/.config/cryptobench/devices.yaml` | outside the repository | `apps/benchmark-runner/pipeline.py` `--devices`, `--session` | fixed; absent is no aliases |
| a `session.yaml` | anywhere; no committed copy | `apps/benchmark-runner/pipeline.py` `--session`, `--check-session` | the flag; its paths resolve against its folder |
| `apps/benchmark-runner/energy/requirements.txt`, `requirements-manafa.txt` | in place, tracked | the `--energy-python` interpreter's install | fixed, beside the energy scripts; installed on first use |
| `apps/benchmark-runner/energy/rails/excluded.yaml` | in place, tracked | `apps/benchmark-runner/energy/rails/selection.py` | fixed, packaged beside its reader |
| `requirements.txt` | in place, tracked | `pip install -r`, CI | fixed, at the repository root |
| `lib/cryptobench/cryptobench/shared/settings/defaults.yaml` | never: the config module's `-Dexamples.update` run writes it | the runner and perf-repair, as package data | package data |

Fields and precedence of the benchmark files: [config.md](../apps/benchmark/modules/config/docs/config.md).
