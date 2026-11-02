# Benchmark for Android crypto primitives

[![jca contract](https://github.com/JuneKim0007/cryptobenchmark/actions/workflows/jca-contract.yml/badge.svg)](https://github.com/JuneKim0007/cryptobenchmark/actions/workflows/jca-contract.yml)
[![modules](https://github.com/JuneKim0007/cryptobenchmark/actions/workflows/modules.yml/badge.svg)](https://github.com/JuneKim0007/cryptobenchmark/actions/workflows/modules.yml)
[![docs](https://github.com/JuneKim0007/cryptobenchmark/actions/workflows/docs.yml/badge.svg)](https://github.com/JuneKim0007/cryptobenchmark/actions/workflows/docs.yml)

Measures the JCA cryptographic primitives a JVM or an Android device provides: what is registered, what runs, and how fast.

```mermaid
flowchart LR
    D[discovery] -- capture, trial --> C[config] -- effective --> P[preparation] --> B[benchmark] --> A[analysis]
```

| read | for |
|---|---|
| [docs/run.md](docs/run.md) | prerequisites, `scripts/pipeline.py` flags, `scripts/demo.sh`, device runs |
| [docs/architecture.md](docs/architecture.md) | modules, dependencies, stage files |
| [docs/results.md](docs/results.md) | `results/<device_id>/` layout and `manifest.yaml` |
| [docs/cryptography/index.md](docs/cryptography/index.md) | configured primitives and providers |
| [docs/index.md](docs/index.md) | every cross-module doc |
| [perf-repair/README.md](perf-repair/README.md) | crypto replacements worth testing in an app |
