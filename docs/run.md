# Run

## Prerequisites

| need | value |
|---|---|
| Java | 17 toolchain target; Kotlin comes from the Gradle plugin `kotlin("jvm")` 2.2.21 |
| host Python deps | `scripts/requirements.txt`: PyYAML>=6, matplotlib>=3.7 |
| energy Python deps | `tools/energy/requirements.txt`, see [energy.md](energy.md) |
| `ANDROID_HOME` (`--device`) | default `~/Library/Android/sdk`; adb at `$ANDROID_HOME/platform-tools/adb` |
| device state (`--device`) | `adb get-state` must print `device` |
| `ANDROID_SERIAL` (`--device`) | selects one device; several attached and none selected stops with `several_devices`; a serial not attached stops with `device_not_attached` |
| root (`--device`) | not required: the app creates its own files directory; shell reads it through group `ext_data_rw` |

## scripts/pipeline.py

```
python3 scripts/pipeline.py [--config PATH] [--results DIR] [--discovery overwrite|keep|reuse]
                            [--bench | --device] [--suppress-errors ERRORS] [--energy-python PYTHON]
                            [--energy-accept-unresponsive] [--stacktrace] [--stream] [--harness HARNESS_YAML]
                            [--interop PLAN_YAML]
```

| flag | default | effect |
|---|---|---|
| `--config PATH` | `$CRYPTOBENCH_CONFIG`, then `~/.config/cryptobench/global.yaml`, then `config/global.yaml` | the `global.yaml` to run |
| `--results DIR` | `<repo>/results` | results root; the run writes `<DIR>/<device_id>/` ([results.md](results.md#device-folder)) |
| `--discovery` | `overwrite` | `overwrite` clears `discovery/` first; `keep` adds a new capture; `reuse` keeps this device's capture, found by asking the JVM for its id first |
| `--bench` | off | also prepare, measure and analyse on the JVM via quick-bench |
| `--device` | off | probe, prepare and measure on the attached device over adb |
| `--suppress-errors ERRORS` | `""` | passed as `androidx.benchmark.suppressErrors`, e.g. `EMULATOR,UNLOCKED`; numbers are then not comparable |
| `--energy-python PYTHON` | `sys.executable` | interpreter with `tools/energy/requirements.txt` installed |
| `--energy-accept-unresponsive` | off | run energy cases on unresponsive rails, see [energy.md](energy.md#pre-flight) |
| `--stacktrace` | off | print the tool's full output on failure |
| `--stream` | off | show each tool's progress |
| `--harness HARNESS_YAML` | off | with `--device`: generate, install and measure perf-repair's scopes instead of the plan's cases, see [scoped.md](../modules/android/docs/scoped.md) |
| `--interop PLAN_YAML` | off | with `--bench` or `--device`: discover, then check perf-repair's `interop_plan.yaml` pairs instead of measuring, see [interop.md](../modules/preparation/docs/interop.md) |

| rule | result |
|---|---|
| `--bench` with `--device` | rejected (mutually exclusive) |
| `--device` with `--discovery reuse` | fails |
| `--suppress-errors` or `--energy-accept-unresponsive` without `--device` | fails |
| energy capture other than `none` without `--device` | fails |
| `--harness` without `--device` | fails |
| `--harness` with `--results` | fails: `measured/` goes beside `harness.yaml` |
| `--interop` without `--bench` or `--device`, or with `--harness` | fails |
| neither `--bench` nor `--device` | discover and configure only, then a manifest that replaces the device's last one |
| any failure | prints `error: <message>`, exits 1 |

- Host discovery runs `ProbeKt`; `--discovery reuse` runs `RuntimeFieldsKt` first, then adds `--reuse`.
- Device discovery runs `ConfigureKt` with `--facts`.
- `run.processRepetitions` ([config.md](../modules/config/docs/config.md)) above 1: runs merged with `MergeRunsKt`.
- Tool commands: [tools.md](tools.md). Output: [results.md](results.md).
- Analysis runs `analyze.py`, then `charts.py` ([tools.md](tools.md#chartspy)).

## scripts/explain.py

```
python3 scripts/explain.py [--config PATH] [--results DIR] [--device-id ID]
```

- Prints the run id, each `run`, `policy` and `analysis` key of `<results>/<device_id>/configuration/effective.yaml` with its value and source: the global file when written there, else `default`.
- Ends with the entry count and the test set.
- A root with several device folders needs `--device-id`, else `several_device_results`.

## scripts/demo.sh

| flag | effect |
|---|---|
| none | `config/global-quick.yaml` (11 test-set entries, about 30 s), `results/demo/<device_id>`, `--discovery overwrite` |
| `--warm` | compile both tools, exit |
| `--fast` | `config/global-demo.yaml`: `testsets/smoke.yaml` (3 entries), `inputSizes [1024]`, about 8 s |
| `--reuse` | `--discovery reuse` |
| `--config FILE` | another `global.yaml` |
| `--results DIR` | another results root |
| `-h`, `--help` | usage |

- Runs `pipeline.py --bench --stream`, then prints the head of `results/demo/<device_id>/analysis/summary.md`.

## Device run

| step | command or path |
|---|---|
| install | root `gradlew :android:installRelease :android:installReleaseAndroidTest`, plus `-PbundledArtifacts=<artifact>,...` when global.yaml has `providers.bundled` |
| bundled providers | `DeviceProbe` gets `-e bundledProviders '<json>'`; after configure, `effective.yaml` `bundledProviders` must equal the built list, else `bundled_mismatch` |
| plan and androidx output directories | by API level: `modules/android/docs/harness.md#device-directories` |
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
