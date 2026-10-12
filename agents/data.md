# Data

## Calls
- `docs/artifacts.md` : every artifact: producer, consumers, validator

## Rules
- boundary: perf-repair reads cryptobenchmark only through `results/manifest.yaml` and the files it lists.
- dto: no I/O; every file-level document carries `schemaVersion` and its reader refuses another.
- numbers: summarised once in `inbound/results.py`; nothing downstream recomputes them.
- gate: the inbound command writes nothing until the manifest, rows, measurements and run log validate.

## Workflow
- add an artifact: dto → name in `src/perfrepair/run_dir.py` → validator (`agents/validation.md`) → row in `docs/artifacts.md`

## File structure

```
src/perfrepair/data_handler/inbound/__main__.py : command: manifest → rows.json, measurements.json, run_log.json, sites.json; validated before writing
src/perfrepair/data_handler/inbound/app_source.py : JCA getInstance call sites in an app tree; default provider by manifest precedence
src/perfrepair/data_handler/inbound/manifest.py : reads manifest.yaml; resolves a files key to a path
src/perfrepair/data_handler/inbound/probe_index.py : probe → engine types and name/alias index per provider
src/perfrepair/data_handler/inbound/results.py : benchmark.json + prepared.yaml → PrimitiveRows and Summaries; comparability notes
src/perfrepair/data_handler/inbound/run_log.py : skipped, unmeasured, not-runnable and measured records → deduplicated RunLog
src/perfrepair/data_handler/outbound/benchmark_runner.py : runs cryptobenchmark pipeline.py; returns the manifest path
src/perfrepair/data_handler/outbound/run_config.py : writes generated_perf_repair.yaml from a base global.yaml
src/perfrepair/dto/grouping.py : Family, Item, Profile; items.json and profiles.json documents
src/perfrepair/dto/grouping_output.py : Finding and checks.json
src/perfrepair/dto/grouping_state.py : Answer, Amendment, OutboxRecord, Group, Knowledge
src/perfrepair/dto/manifest.py : BenchmarkManifest: the manifest.yaml contract with cryptobenchmark
src/perfrepair/dto/measurement.py : Summary and the Measurements document
src/perfrepair/dto/primitive.py : PrimitiveRow: one measured configuration, no numbers
src/perfrepair/dto/run_log.py : LogEntry, RunLog, statuses
src/perfrepair/dto/worthiness.py : GroupEvidence, PairMetrics, Verdict, Verdicts
src/perfrepair/files.py : JSON read and atomic write
src/perfrepair/run_dir.py : run directory: artifact names and loaders
```
