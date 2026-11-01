# Pipeline

## Diagram

```mermaid
flowchart LR
    O[outbound: run_config, benchmark_runner] -- generated_perf_repair.yaml --> B[cryptobenchmark pipeline.py]
    B -- results/manifest.yaml --> I[inbound]
    B -- manifest --> G[grouping: build, assign per item, report]
    I -- rows, measurements --> E[evidence + triage: static]
    G -- grouping/groups.json --> E
    E -- groups with an improving pair --> W[worthiness: model per group]
    E -- static verdicts --> V[worthiness-mode/verdicts.json]
    W --> V
    I -- sites.json --> R[repair: candidates, choose, edit, harness]
    G -- grouping/groups.json --> R
    V --> R
```

## Stages

| Stage | Command | Reads | Writes | Model |
|---|---|---|---|---|
| outbound | `data_handler.outbound` (library) | base `global.yaml`, `config/testsets/all.yaml` default test set | `generated_perf_repair.yaml`, benchmark `results/` | no |
| inbound | `python3 -m perfrepair.data_handler.inbound --manifest <m> [--app <src>] -o <run>` | `manifest.yaml` and its files; the app tree | `rows.json`, `measurements.json`, `run_log.json`; `sites.json` with `--app` | no |
| grouping build | `python3 -m perfrepair.grouping build --manifest <m> --run <run>` | `manifest.yaml` and its files | `grouping/items.json`, `profiles.json` | no |
| grouping assign | `python3 -m perfrepair.grouping assign --run <run>` | `grouping/` | `grouping/` (`docs/grouping.md`) | one conversation per item, up to turns × sessions |
| grouping report | `python3 -m perfrepair.grouping report --run <run> [--supervisor]` | `grouping/` | `checks.json`, `groups.json`; supervisor files | supervisor: one conversation per family |
| worthiness | `python3 -m perfrepair.ai worthiness --run <run> --mode latency\|battery` | `rows.json`, `measurements.json`, `grouping/groups.json` | `worthiness-<mode>/` (evidence.json, outbox/, verdicts.json, journal.jsonl, errors.jsonl) | one per group with an improving pair |
| repair | `python3 -m perfrepair.repair candidates\|test-set\|choose\|edit\|harness\|replay` | `docs/repair.md` | `repair/<app>/`, `apps/<app>/` | no |
| validate | `python3 -m perfrepair.validation <run>` | every artifact present | nothing | no |

- `grouping assign`, `grouping report` and `ai worthiness` accept `--agent dry-run` in place of a model.
- Inbound, grouping build and repair edit and harness validate before they write.
- A rerun of `grouping assign` or `ai worthiness` with the same prompts resumes after the last record of that charter's outbox; changed prompts start a new outbox, and an earlier prompt set resumes its own.
- `--prompts DIR`: `docs/decisions.md`.
