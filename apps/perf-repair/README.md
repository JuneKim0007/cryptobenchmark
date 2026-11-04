# perf-repair

Reads cryptobenchmark results for one device and decides which crypto replacements are worth testing in an app, for the metrics its perfMode selects (latency, throughput, memAlloc, energy, or generic).
Location: `apps/perf-repair/` inside the cryptobenchmark repo; the benchmark is found two levels up, `CRYPTOBENCH_ROOT` overrides.

## Setup

- `pip install -r requirements.txt` from the repository root: every host Python dependency, Python 3.10+.
- `pip install -e .` puts `perfrepair` on the path for `python3 -m perfrepair`; without the tree-sitter pins a scope's lifecycle is `unsupported`.
- Copy `perfrepair.example.yaml` to `perfrepair.yaml` for the gateway, auth, model, effort per command, default paths, and the `device` and `apps` settings; `.env` (from `.env.example`) still works and holds `ANTHROPIC_API_KEY`. Precedence: `docs/settings.md`.
- `make check` runs docs-lint and the tests.

| gateway (`--agent`), auth (`--auth`) | needs |
|---|---|
| `claude`, `subscription` (default) | the logged-in `claude` CLI; `ANTHROPIC_API_KEY` is withheld from it |
| `claude`, `api` | `ANTHROPIC_API_KEY`, `anthropic` from `requirements.txt` |
| `dry-run` | nothing; no model is called |

## Usage

Benchmark then every target app, from one settings file: `python3 scripts/facade.py --settings settings.yaml` ([facade](../../docs/facade.md)).

The lower-level command, once `pip install -e .` (or `PYTHONPATH=src`) puts the package on the path:

```
python3 -m perfrepair guide --app <app root> --device-results <results root>/<device id> [--perf-mode generic|<keys>] [--device]
python3 -m perfrepair guide --device-results <results root>/<device id>   # without --app: every apps.targets entry
```

Without `--device` it ends at `harness.yaml`; `--device` needs an attached phone. Steps and stop codes: `docs/replacement.md`.

## Docs

Commands per stage: `docs/pipeline.md`. All facts: `docs/index.md`.
