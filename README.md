# Benchmark for Android crypto primitives

[![jca contract](https://github.com/JuneKim0007/cryptobenchmark/actions/workflows/jca-contract.yml/badge.svg)](https://github.com/JuneKim0007/cryptobenchmark/actions/workflows/jca-contract.yml)
[![modules](https://github.com/JuneKim0007/cryptobenchmark/actions/workflows/modules.yml/badge.svg)](https://github.com/JuneKim0007/cryptobenchmark/actions/workflows/modules.yml)
[![docs](https://github.com/JuneKim0007/cryptobenchmark/actions/workflows/docs.yml/badge.svg)](https://github.com/JuneKim0007/cryptobenchmark/actions/workflows/docs.yml)

Measures the JCA cryptographic primitives a JVM or an Android device provides: what is registered, what runs, and how fast.

```mermaid
flowchart LR
    D[discovery] -- capture, trial --> C[config] -- effective --> P[preparation] --> B[benchmark] --> A[analysis]
```

## Setup

```
pip install -r requirements.txt
```

## First run

```
cp settings.example.yaml settings.yaml
cp apps/perf-repair/perfrepair.example.yaml apps/perf-repair/perfrepair.yaml   # set apps.targets
python3 apps/cli/facade.py --settings settings.yaml --check           # the resolved tree; no app build, device or model
python3 apps/cli/facade.py --settings settings.yaml                   # benchmark, then guided repair
```

| read | for |
|---|---|
| [docs/facade.md](docs/facade.md) | the settings index, its direction rule, the phases |
| [docs/run.md](docs/run.md) | prerequisites, `apps/benchmark-runner/pipeline.py` flags, `apps/benchmark-runner/demo.sh`, device runs |
| [docs/architecture.md](docs/architecture.md) | modules, dependencies, stage files |
| [docs/results.md](docs/results.md) | `results/<device_id>/` layout and `manifest.yaml` |
| [docs/cryptography/index.md](docs/cryptography/index.md) | configured primitives and providers |
| [docs/index.md](docs/index.md) | every cross-module doc |
| [apps/perf-repair/README.md](apps/perf-repair/README.md) | crypto replacements worth testing in an app |

## Fixed behavior

These are not settings.

- GC stays on; a full collection is forced between iters with the timer stopped, so one rarely lands inside an iter, and the pause is reported beside the time.
- The app and every bundled provider are compiled ahead of time (`speed`) before measuring.
- Energy is always measured in its own pass, traced and without forced collections; timing is never traced.
- A process prepares only the case it runs, so another case's keys or failures can't affect it.
- A launch whose warm-up left unusably short iters is measured once more, then recorded as failed.

## Assumptions

- AOT: real apps start JIT- or profile-compiled, so their first calls can be slower than these numbers.
- Garbage collection: a real app pays for collection inside its own work; this cost is reported beside the number, not in it.
- CPU: the measuring thread stays on one big core; a real app's thread moves between core types.
- Clocks: on an unrooted phone clocks can't be locked, so numbers assume the governor holds the core at full speed.
- Temperature: the phone is assumed not to be throttling; temperature is recorded for each case, and held to a limit only with `run.thermalGate`.
- Keys: each launch generates its own key, so key-dependent algorithms (RSA, ECDSA) also vary from key to key.
