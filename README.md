# perf-repair

Reads cryptobenchmark results for one device and decides which crypto replacements are worth testing in an app, under a latency-first or battery-first criterion. Static tools compute everything; a model, called once per item with no history, only decides.

## Run

```
python3 -m perfrepair.data_handler.inbound --manifest <benchmark results>/manifest.yaml -o <run>
python3 -m perfrepair.grouping build --manifest <benchmark results>/manifest.yaml --run <run>
python3 -m perfrepair.grouping assign --run <run>
python3 -m perfrepair.grouping report --run <run> [--supervisor]
python3 -m perfrepair.orchestrate worthiness --run <run> --mode latency
python3 -m perfrepair.orchestrate worthiness --run <run> --mode battery
python3 -m perfrepair.validation <run>
```

Model backend: copy `.env.example` to `.env`. `claude-code` (default) uses a Claude subscription through the logged-in `claude` CLI; `claude` uses the Anthropic API with `ANTHROPIC_API_KEY` (`pip install -e .[api]`); `dry-run` calls no model. `--agent` overrides per command.

Requires Python 3.10+, `pyyaml`, `anthropic` for model calls. `make check` runs docs-lint and the tests.

## Docs

Agents and contributors start at `AGENTS.md`; facts are in `docs/index.md`.
