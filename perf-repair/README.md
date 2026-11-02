# perf-repair

Reads cryptobenchmark results for one device and decides which crypto replacements are worth testing in an app, in latency or battery mode.
Location: `perf-repair/` inside the cryptobenchmark repo; the benchmark is found one level up, `CRYPTOBENCH_ROOT` overrides.

## Setup

- Python 3.10+, `pyyaml`; `pip install -e .[test]` for tests.
- Copy `perfrepair.example.yaml` to `perfrepair.yaml` for the backend, model, effort per command and default paths; `.env` (from `.env.example`) still works and holds `ANTHROPIC_API_KEY`. Precedence: `docs/settings.md`.
- `make check` runs docs-lint and the tests.

| backend (`--agent`) | needs |
|---|---|
| `claude-code` (default) | the logged-in `claude` CLI; `ANTHROPIC_API_KEY` is withheld from it |
| `claude` | `ANTHROPIC_API_KEY`, `pip install -e .[api]` |
| `dry-run` | nothing; no model is called |

## Usage

One app from source to a measured report, after inbound and grouping have filled the run:

```
python3 scripts/llm_guide.py --app <app root> --name <app> --run ~/capstone/runs/<date>-<name> \
    --results <cryptobenchmark results> [--mode latency|battery] [--device]
```

`python3 -m perfrepair guide` takes the same arguments once `pip install -e .` (or `PYTHONPATH=src`) puts the package on the path. Without `--device` it ends at `harness.yaml`; `--device` needs an attached phone. Steps and stop codes: `docs/replacement.md`.

## Docs

Commands per stage: `docs/pipeline.md`. All facts: `docs/index.md`.
