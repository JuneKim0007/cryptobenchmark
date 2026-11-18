# Run

## Prerequisites

| need | value |
|---|---|
| Java | 17 toolchain target; Kotlin comes from the Gradle plugin `kotlin("jvm")` 2.2.21 |
| host Python deps | `pip install -r requirements.txt`; a missing module a run needs is `missing_dependency: <module>; pip install -r requirements.txt` and exit 1 at its start (`apps/benchmark-runner/dependencies.py`); a `cryptobench` loaded from outside this checkout's `lib/cryptobench` is `library_outside_checkout` and exit 1 |
| energy Python deps | in `requirements.txt`; `apps/benchmark-runner/energy/requirements.txt` for a separate `--energy-python`, see [energy.md](energy.md) |
| `ANDROID_HOME` (`--device`) | default `~/Library/Android/sdk`; adb at `$ANDROID_HOME/platform-tools/adb` |
| device state (`--device`) | `adb get-state` must print `device` |
| `ANDROID_SERIAL` (`--device`) | selects one device; several attached and none selected stops with `several_devices`; a serial not attached stops with `device_not_attached` |
| root (`--device`) | not required: the app creates its own files directory; shell reads it through group `ext_data_rw` |

## apps/benchmark-runner/pipeline.py

The command for both sides is `apps/cli/facade.py` ([facade.md](facade.md)); this one is the benchmark's own.
```
python3 apps/benchmark-runner/pipeline.py [--config PATH] [--results DIR] [--discovery overwrite|keep|reuse|verify] [--probe-store DIR]
                            [--bench | --device] [--suppress-errors ERRORS] [--energy-python PYTHON]
                            [--energy-accept-unresponsive] [--reconnect-wait-minutes M] [--reconnect-poll-seconds S]
                            [--stacktrace] [--stream] [--harness HARNESS_YAML] [--interop PLAN_YAML] [--probe] [--identify] [--devices] [--check-session SESSION_YAML] [--session SESSION_YAML] [--per-suite]
```

| flag | default | effect |
|---|---|---|
| `--config PATH` | `$CRYPTOBENCH_CONFIG`, then `~/.config/cryptobench/global.yaml`, then `config/global.yaml` | the `global.yaml` to run; one named by the flag or the variable and missing is `missing_file` |
| `--results DIR`, `--per-suite` | `<repo>/results`, off | results root; the run writes `<DIR>/<device_id>/`, with `--per-suite` `<DIR>/<device_id>/<suite>/` ([results.md](results.md#device-folder)); `--per-suite` with `--identify` or `--harness` fails |
| `--discovery` | `overwrite` | `overwrite` starts an empty `discovery/`, the old one moving aside with its unit ([results.md](results.md#device-folder)); `keep` adds a new capture; `reuse` keeps this device's capture, found by asking the JVM for its id first; `verify` as `overwrite` but reusing a stored probe ([Probe store](#probe-store)) |
| `--probe-store DIR` | off | `--discovery verify` only: one capture+trial per build key, shared by every run that names it |
| `--bench` | off | also prepare, measure and analyse on the JVM via the benchmark CLI (`BenchKt`) |
| `--device` | off | probe, prepare and measure on the attached device over adb |
| `--probe` | off | discovery and configure only, with `--device` on the device; the device folder and its manifest, nothing measured |
| `--identify` | off | one line `identity:  {code, config, deviceId, harness, inputs, mode}` (JSON), `code` `{timed, runner}` as in the run record ([results.md](results.md#resuming-a-stopped-run)), `harness` the digest of the files `lib/cryptobench/cryptobench/stages/verification/scope/code_digest.py` names, and nothing written: `getprop` on a device, `RuntimeFieldsKt` on a host; the id the probe would give |
| `--devices`, `--check-session SESSION_YAML`, `--session SESSION_YAML` | off | what adb sees ([devices.md](devices.md)); a session's plan and skips; a session's run ([sessions.md](sessions.md)); each before the global.yaml is read; with `--config` or any mode fails |
| `--suppress-errors ERRORS` | `CRYPTOBENCH_SUPPRESS_ERRORS`, else `""` | passed as `androidx.benchmark.suppressErrors`, e.g. `EMULATOR,UNLOCKED`; numbers are then not comparable; part of a resumed run's identity ([results.md](results.md#resuming-a-stopped-run)); the variable reaches a run the guide or facade starts |
| `--energy-python PYTHON` | `sys.executable`, else the source's cached venv ([energy.md](energy.md)) | interpreter with `apps/benchmark-runner/energy/requirements.txt` installed; `requirements-manafa.txt` too for `energy.source: manafa` |
| `--energy-accept-unresponsive` | off | run energy cases on unresponsive rails, see [energy.md](energy.md#pre-flight); part of the run record ([results.md](results.md#resuming-a-stopped-run)) |
| `--reconnect-wait-minutes M`, `--reconnect-poll-seconds S` | 60, 10 (`lib/cryptobench/cryptobench/stages/measurement/session/reconnect.py`) | `--device`: how long a lost adb transport is waited for before the run stops, and how often `adb get-state` is asked meanwhile ([device-session.md](device-session.md#lost-device)); without `--device` or negative fails |
| `--stacktrace`, `--stream` | off | print the tool's full output on failure; show each tool's progress |
| `--harness HARNESS_YAML` | off | with `--device`: generate, compile, install and interop-check perf-repair's scopes, original against patched, instead of the plan's cases; nothing is timed, see [scoped.md](../apps/benchmark/modules/android/docs/scoped.md) |
| `--interop PLAN_YAML` | off | with `--bench` or `--device`: discover, then check perf-repair's `interop_plan.yaml` pairs instead of measuring, see [interop.md](../apps/benchmark/modules/preparation/docs/interop.md) |

| rule | result |
|---|---|
| `--bench` with `--device` | rejected (mutually exclusive) |
| `--device` with `--discovery reuse`; `--discovery verify` without `--device` and `--probe-store`; `--probe-store` without `verify` | fails |
| `--suppress-errors` without `--device` or `--session`, `--energy-accept-unresponsive` without `--device` | fails |
| energy capture other than `none` without `--device` | fails |
| `--harness` without `--device`, or with `--results` | fails: `checked/` goes beside `harness.yaml` |
| `--interop` without `--bench` or `--device`, or with `--harness` | fails |
| `--probe` or `--identify` with `--bench`, `--harness` or `--interop` | fails |
| `global.yaml` or its test set refused by `CheckConfigKt`, any run but `--identify` | one line before any build |
| `--probe`, or neither `--bench` nor `--device` | discover and configure only, then a manifest; the device's last unit moved aside first ([results.md](results.md#device-folder)) |
| any failure | prints `error: <message>`, exits 1; an error with no code of its own is `subprocess_failed: <command> exited <n>` or `internal_error: <type>: <message>`, with the traceback under `--stacktrace` |

- Host discovery runs `ProbeKt`; `--discovery reuse` runs `RuntimeFieldsKt` first, then adds `--reuse`; with no kept capture that fits the JVM's runtime it probes again and prints `warning: discovery_reprobed: ...`.
- Device discovery runs `ConfigureKt` with `--facts`. The run's capture is the one its discovery wrote: on a host the file `ProbeKt` printed, on a device the one capture the probe added to `discovery/`; its trial and requirements are the files with the same stamp. With `--discovery keep` older captures stay beside it and are never picked by their stamp, which comes from the host on a device run; `deviceClockMillis` keeps the device clock beside it.
- `run.processRepetitions` ([config.md](../apps/benchmark/modules/config/docs/config.md)) above 1: runs merged with `MergeRunsKt`.
- Tool commands: [tools.md](tools.md). Output: [results.md](results.md). Every host subprocess runs under a ceiling: [timeouts.md](timeouts.md).

### Probe store

`--discovery verify` (`lib/cryptobench/cryptobench/stages/discovery/probe_store.py`), after the install:

| step | rule |
|---|---|
| key | `ro.build.fingerprint`, the security patch and the apex versionCodes facts.yaml records; sha256 of each installed APK file of the app and the test package by file name (`base.apk`, `split_*.apk`; the install folder is random), read on the device (`pm path`, `sha256sum`), which carry the code and the bundled jars; `providers.bundled`; named by the first 16 hex of its sha256 |
| entry | `<DIR>/<key>/` holds one capture, its trial and requirements, and `key.yaml`: `key` (the key) and `files` (`<file name>: <sha256>` of the three) |
| match | `key.yaml` names this key and each listed file has its sha256: the three are copied unchanged into `discovery/`, the device's `probe_*`, `trial_*` and `requirements_*` are deleted so the plan push leaves the reused pair the newest by name, and no probe runs |
| no match | the probe runs as under `overwrite`, and its capture, trial and requirements are stored under the key (`warning: probe_store_failed: ...` when they cannot be) |
| damaged | `key.yaml` unreadable, without `files` or naming another key, or a listed file missing or with another sha256: `full probe: stored entry <k> is damaged: <file>`, the probe runs and its files replace the entry |
| fallback | an unreadable or empty key part, or no plan directory on the device: the probe runs; nothing is stored when the key is incomplete |
| printed | `discovery: verify: reused <capture>: key <k> matches ...`, or `discovery: verify: full probe: <why>`; with no entry under the key, the dotted key fields (e.g. `device.apex.com.android.conscrypt`) that differ from the newest readable entry of the same `device.fingerprint`, or `no stored entry for fingerprint <f>` |

## apps/benchmark-runner/explain.py

```
python3 apps/benchmark-runner/explain.py [--config PATH] [--results DIR] [--device-id ID]
```

- Prints the run id, each `run`, `policy` and `analysis` key of `<results>/<device_id>/configuration/effective.yaml` with its value and source: the global file when written there, else `default`.
- Ends with the entry count and the test set.
- A root with several device folders needs `--device-id`, else `several_device_results`.

## apps/benchmark-runner/demo.sh

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
| install | `apps/benchmark/gradlew :android:installRelease :android:installReleaseAndroidTest`, plus `-PbundledArtifacts=<artifact>,...` when global.yaml has `providers.bundled` |
| bundled providers | `DeviceProbe` gets `-e bundledProviders '<json>'`; after configure, `effective.yaml` `bundledProviders` must equal the built list, else `bundled_mismatch` |
| plan and androidx output directories | by API level: `apps/benchmark/modules/android/docs/harness.md#device-directories` |
| AOT compile | `cmd package compile -f -m speed` on both APKs, right after the plan push; with energy capture the rails pre-flight and its settle come after it, then `energy.yaml` is pushed, so dex2oat never runs inside the settle |
| profiler | `-e androidx.benchmark.profiling.mode None` |
| pull | whole plan directory into `discovery/` |

### Device session

The benchmark measures through one device session: [device-session.md](device-session.md). A `--harness` run measures nothing: it compiles the scopes and runs `ScopedInterop` once.

| piece | what it is | device time it costs |
|---|---|---|
| session | `lib/cryptobench/cryptobench/stages/measurement/session/measure.py`: processes over repetitions, hooks around each process and case | the sum of its passes |
| passes | `run.passes`: one session per metric group, merged per metric | per case: timing 300 samples about 38 s, energy 100 about 20 s, allocation 100 about 15 to 30 s |
| process per case | one `am instrument` per case | about 1 to 2 s per case and pass, plus the plan's preparation |
| temperature | `dumpsys thermalservice` before and after every process and case, into `benchmark.json` per case | two `dumpsys` calls per case, under a second |
| warm-up | `run.warmup`: a pre-flight of a few cases before the first pass, never measured | about 2 s plus 1 s per case at 10 samples, once per run |
| cool-down | `run.caseCooldownSeconds`: host sleep between measured cases | `(cases - 1) x seconds` per pass |
| thermal gate | `run.thermalGate`: keeps every run of a case under a skin temperature ([device-session.md](device-session.md#thermal-gate)) | every `cooldownMinutes` hold, the polling wait after it, and every discarded run measured again |
| frequency caps | capped cores per case at its start and end in `clocks.yaml` | two sysfs reads per case, tens of ms |

### Recover a metric without a device

`benchmarkData.json` holds `allocationCount` for every case even when `run.metrics` was `[TIME]` ([measure.md](../apps/benchmark/modules/benchmark/docs/measure.md#jetpack-conversion)). Converting it again reports it; nothing runs on the device:

```
D=results/<device_id>
apps/benchmark/gradlew -p apps/benchmark/cli run -q -PmainClass=ConvertKt \
  --args="$D/benchmark/benchmarkData.json $D/preparation/prepared.yaml $D/benchmark $D/benchmark/energy.json --metrics=TIME,ALLOCATION"
```

- Leave `energy.json` out when the run captured no energy.
- With `run.processRepetitions` above 1: once per `process-N/`, then `MergeRunsKt`.
- Then rerun `python3 -m perfrepair.data_handler.inbound --device-results "$D"`; its digests see the new `benchmark.json`.

## Device facts

| fact | rule |
|---|---|
| `rooted` | `su -c id` returns `uid=0` within 5 s |
| `pinning` | release APK contains `lib/<abi>/libaffinity.so`; null with a `pinning_unknown` warning when the APK is absent |
| ABI | `pm dump` `primaryCpuAbi`, else `ro.product.cpu.abi` |
| `cpuLocked` | every online core has `scaling_min_freq == scaling_max_freq` before and after the measure; unreadable gives `unknown` |
