# Run

## Prerequisites

| need | value |
|---|---|
| Java | 17 toolchain target; Kotlin comes from the Gradle plugin `kotlin("jvm")` 2.2.21 |
| host Python deps | `scripts/requirements.txt`: PyYAML>=6, matplotlib>=3.7 |
| energy Python deps | `tools/energy/requirements.txt`, see [energy.md](energy.md) |
| `ANDROID_HOME` (`--device`) | default `~/Library/Android/sdk`; adb at `$ANDROID_HOME/platform-tools/adb` |
| device state (`--device`) | `adb get-state` must print `device` |
| root (`--device`) | not required: the app creates its own files directory; shell reads it through group `ext_data_rw` |

## scripts/pipeline.py

```
python3 scripts/pipeline.py [--config PATH] [--results DIR] [--discovery overwrite|keep|reuse]
                            [--bench | --device] [--suppress-errors ERRORS] [--energy-python PYTHON]
                            [--energy-accept-unresponsive] [--stacktrace] [--stream]
```

| flag | default | effect |
|---|---|---|
| `--config PATH` | `$CRYPTOBENCH_CONFIG`, then `~/.config/cryptobench/global.yaml`, then `config/global.yaml` | the `global.yaml` to run |
| `--results DIR` | `<repo>/results` | output root |
| `--discovery` | `overwrite` | `overwrite` clears `discovery/` first; `keep` adds a new capture; `reuse` keeps this device's capture |
| `--bench` | off | also prepare, measure and analyse on the JVM via quick-bench |
| `--device` | off | probe, prepare and measure on the attached device over adb |
| `--suppress-errors ERRORS` | `""` | passed as `androidx.benchmark.suppressErrors`, e.g. `EMULATOR,UNLOCKED`; numbers are then not comparable |
| `--energy-python PYTHON` | `sys.executable` | interpreter with `tools/energy/requirements.txt` installed |
| `--energy-accept-unresponsive` | off | run energy cases on unresponsive rails, see [energy.md](energy.md#pre-flight) |
| `--stacktrace` | off | print the tool's full output on failure |
| `--stream` | off | show each tool's progress |

| rule | result |
|---|---|
| `--bench` with `--device` | rejected (mutually exclusive) |
| `--device` with `--discovery reuse` | fails |
| `--suppress-errors` or `--energy-accept-unresponsive` without `--device` | fails |
| energy capture other than `none` without `--device` | fails |
| neither `--bench` nor `--device` | discover and configure only, then manifest |
| any failure | prints `error: <message>`, exits 1 |

- Host discovery runs `ProbeKt`; `--discovery reuse` adds `--reuse`.
- Device discovery runs `ConfigureKt` with `--facts`.
- `run.processRepetitions` ([config.md](../modules/config/docs/config.md)) above 1: runs merged with `MergeRunsKt`.
- Tool commands: [tools.md](tools.md). Output: [results.md](results.md).
- Analysis runs `analyze.py`, then `charts.py` ([tools.md](tools.md#chartspy)).

## scripts/explain.py

```
python3 scripts/explain.py [--config PATH] [--results DIR]
```

- Prints the run id, each `run`, `policy` and `analysis` key of `<results>/configuration/effective.yaml` with its value and source: the global file when written there, else `default`.
- Ends with the entry count and the test set.

## scripts/device_args.py

```
python3 scripts/device_args.py [effective.yaml]
```

- Prints one `-Pandroid.testInstrumentationRunnerArguments.<name>=<value>` per line for a Gradle instrumentation launch.
- `CPU_EVENTS` in `run.metrics`: `androidx.benchmark.cpuEventCounter.enable=true`; otherwise nothing.
- `pipeline.py --device` does not call it.

## scripts/demo.sh

| flag | effect |
|---|---|
| none | `config/global-quick.yaml` (11 test-set entries, about 30 s), `results/demo`, `--discovery overwrite` |
| `--warm` | compile both tools, exit |
| `--fast` | `config/global-demo.yaml`: `testsets/smoke.yaml` (3 entries), `inputSizes [1024]`, about 8 s |
| `--reuse` | `--discovery reuse` |
| `--config FILE` | another `global.yaml` |
| `--results DIR` | another output root |
| `-h`, `--help` | usage |

- Runs `pipeline.py --bench --stream`, then prints the head of `results/demo/analysis/summary.md`.

## Device run

| step | command or path |
|---|---|
| install | root `gradlew :android:installRelease :android:installReleaseAndroidTest` |
| plan directory | `/sdcard/Android/data/io.github.junekim0007.cryptobench/files/cryptobench` |
| androidx output | `/sdcard/Android/media/io.github.junekim0007.cryptobench` |
| AOT compile | `cmd package compile -f -m speed` on both APKs |
| profiler | `-e androidx.benchmark.profiling.mode None` |
| pull | whole plan directory into `discovery/` |

- `CryptoBenchmark` partial failures become warnings; all failed raises.

## Device facts

| fact | rule |
|---|---|
| `rooted` | `su -c id` returns `uid=0` within 5 s |
| `pinning` | release APK contains `lib/<abi>/libaffinity.so` |
| ABI | `pm dump` `primaryCpuAbi`, else `ro.product.cpu.abi` |
| `cpuLocked` | every online core has `scaling_min_freq == scaling_max_freq` before and after the measure; unreadable gives `unknown` |
