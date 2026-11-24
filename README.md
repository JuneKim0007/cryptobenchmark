# Benchmark for Android crypto primitives

[![jca contract](https://github.com/JuneKim0007/cryptobenchmark/actions/workflows/jca-contract.yml/badge.svg)](https://github.com/JuneKim0007/cryptobenchmark/actions/workflows/jca-contract.yml)
[![modules](https://github.com/JuneKim0007/cryptobenchmark/actions/workflows/modules.yml/badge.svg)](https://github.com/JuneKim0007/cryptobenchmark/actions/workflows/modules.yml)
[![docs](https://github.com/JuneKim0007/cryptobenchmark/actions/workflows/docs.yml/badge.svg)](https://github.com/JuneKim0007/cryptobenchmark/actions/workflows/docs.yml)

Measures the JCA cryptographic primitives a JVM or an Android device provides: what is registered, what runs, and how fast.

## Setup

```
pip install -r requirements.txt
```

## First run

```
cp config/facade/settings.example.yaml config/facade/settings.yaml
cp config/perf-repair/perfrepair.example.yaml config/perf-repair/perfrepair.yaml   # set apps.targets
python3 apps/cli/facade.py --settings config/facade/settings.yaml --check   # the resolved tree; no app build, device or model
python3 apps/cli/facade.py --settings config/facade/settings.yaml           # benchmark, then guided repair
```

| read | for |
|---|---|
| [docs/facade.md](docs/facade.md) | the settings index, its direction rule, the phases |
| [docs/run.md](docs/run.md) | prerequisites, `apps/benchmark-runner/pipeline.py` flags, device runs |
| [docs/architecture.md](docs/architecture.md) | modules, dependencies, stage files |
| [docs/results.md](docs/results.md) | `results/<device_id>/` layout and `manifest.yaml` |
| [docs/index.md](docs/index.md) | every cross-module doc |
| [apps/perf-repair/README.md](apps/perf-repair/README.md) | crypto replacements worth testing in an app |

## Recommended settings

- **Set `run.thermalGate` on a phone, and find its temperature for your device.** A hot phone caps its CPU frequency, so numbers shift silently; how to find the threshold and set `temperatureKeptCelsius`: [Thermal gate](docs/device-session.md#thermal-gate).
- **Give very short algorithms more runs.** A case contains runs and a run contains iters. Fast hashes and MACs vary more from run to run than slow operations do, and more iters do not fix that: the extra launches do. `run.processRepetitions` sets one count for every case.

## Connected device setup

- Turn on airplane mode.
- Keep the charger connected for the whole run.
- Start with the battery at 95% or more.
- Enable USB debugging and connect over USB.
- Close every other instance of the benchmark app.
- Do not touch or move the phone while a run measures.

## Fixed behavior

These are not settings.

- A full GC is forced between iters, outside the timer; GC pauses are reported beside the time.
- The app and every bundled provider are compiled ahead of time (`speed`) before measuring.
- Energy is measured in its own pass; timing is never traced.
- Energy windows are at least 5 s (`run.passes.energy.minWindowSeconds`).
- Each process prepares and measures one case.
- Each process runs its cases in an order shuffled from `run.orderSeed`; an algorithm's fixed and notFixed cases run back to back.
- A failed launch is retried `run.launchRetries` times.
- A launch with too-short iters after warm-up is measured once more, then recorded as failed.
- A run with fewer samples than asked is relaunched.
- A failed attempt is kept in `rejected/` with its reason.
- A stopped run resumes from its finished blocks.
- One run at a time per phone.
- Every skipped case is recorded with its code in `skipped.yaml`.

## Adding an algorithm

1. Spellings: its canonical name and every spelling under its engine type in `algorithms/name-index.yaml` (`spellings`, a key-size spelling under `sized`), from a source the file's header lists.
2. Entry: `<type>|<canonical>` in its family's `algorithms/<family>_catalogue.yaml`; the family's group members are its catalogue's entries.
3. Exemplar, optional: the family's `exemplars` in `algorithms/groups.yaml`.
4. Build differences: the entry's `providers` section, or its id in a deviation of `algorithms/deviations.yaml`.
5. Provider aliases come from the capture, never copied into these files.
6. Checks: `make -C apps/perf-repair check`, `apps/benchmark/gradlew -p apps/benchmark :document:test :config:test`, `python3 tools/docs_lint.py`.

## Assumptions

- Real apps start JIT- or profile-compiled; these numbers are ahead-of-time compiled.
- GC cost is reported beside the time, not in it.
- The measuring thread stays on one big core.
- Clocks are not locked.
- The phone is assumed not to throttle; temperature is recorded per case and held only with `run.thermalGate`.
- Each launch generates its own key.
- Every timed call processes one complete message of the case's input size: throughput is per-message, not bulk streaming of one long input through one initialized engine.
- IVs for encryption come from a pool of 256 drawn before the timer and reused in turn; no path times drawing an IV.
