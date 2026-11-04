# Device runs

## Calls
- `docs/run.md` : prerequisites, `scripts/pipeline.py` flags, device requirements
- `docs/device-session.md` : the device session: passes, a process per case, temperature, warm-up
- `docs/results.md` : results/ layout, manifest.yaml, clocks.yaml, facts.yaml
- `docs/energy.md` : capture modes, rail pre-flight, joules output
- `modules/android/docs/index.md` : instrumentation harness and device plan
- `modules/settings/docs/index.md` : `cpu` and `energy` harness keys and device support

## Rules
- entry: run device work through `python3 scripts/pipeline.py --device`; never drive the adb steps of `scripts/device/adb.py` by hand.
- sdk: set `ANDROID_HOME` before a device run; `adb get-state` must report `device`.
- serial: with several devices attached, set `ANDROID_SERIAL` to one.
- root: a device run needs no root; never require it in code or scripts.
- discovery: `--device` probes the attached device; never combine it with `--discovery reuse`.
- suppress-errors: pass `--suppress-errors EMULATOR,UNLOCKED` only on an emulator or a device with unlocked clocks.
- suppress-errors: never compare numbers from a suppressed run with a locked device's.
- clocks: read `cpuLocked` in `results/<device_id>/manifest.yaml` before comparing two device runs.
- isolation: leave `run.isolation: case` on a device run, so a case that crashes its process loses only itself (`docs/device-session.md#one-process-per-case`); set `run` only to measure every case in one process on purpose.
- pinning: request a core through `harness.cpu` (`core: <index>|big`, `required`) in `config/`, never in code.
- pinning: a pinned run needs `libaffinity.so` in the installed release APK; check `pinning` in `discovery/facts.yaml`.
- pinning: report a pinned run as pinned, never as core-isolated; pinning restricts the measuring thread only.
- energy: set `harness.energy.capture` only for `--device` runs; pass `--energy-python` an interpreter with `tools/energy/requirements.txt` installed, plus `tools/energy/requirements-manafa.txt` for `harness.energy.source: manafa`.
