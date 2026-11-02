# Data

## Calls
- `docs/artifacts.md` : every artifact: producer, consumers, validator

## Rules
- boundary: perf-repair reads cryptobenchmark only through `results/manifest.yaml` and the files it lists.
- dto: no I/O; every file-level document carries `schemaVersion` and its reader refuses another.
- numbers: summarised once in `inbound/results.py`; nothing downstream recomputes them.
- gate: the inbound command writes nothing until the manifest, rows, measurements and run log validate.
- names: every algorithm-name comparison goes through `catalog/names.py`; config's `AlgorithmNames.kt` reads the same file and must resolve `tests/fixtures/algorithm-names-cases.yaml` alike.
- names: a spelling goes in `catalog/algorithm-names.yaml` with a cited source; parameters (OAEP, MGF1, provider defaults) never do.
- names: a probe alias the catalog or another provider contradicts is `name_conflict` where it is used, never a pick.

## Workflow
- add an artifact: dto → name in `src/perfrepair/run_dir.py` → validator (`agents/validation.md`) → row in `docs/artifacts.md`

## File structure

```
src/perfrepair/catalog/algorithm-names.yaml : canonical name ← spellings per engine type; key-size suffixes; transformation modes, paddings, per-algorithm synonyms; key formats
src/perfrepair/catalog/names.py : the names reader: Canonical (name, keySize, known), fold, key formats, name_conflict
src/perfrepair/catalog/probe_names.py : the probe's aliases merged onto the catalog; contradictions recorded as conflicts
src/perfrepair/data_handler/inbound/__main__.py : command: manifest → rows.json, measurements.json, run_log.json, validated before writing
src/perfrepair/data_handler/inbound/bootstrap.py : median bootstrap that resamples processes, then blocks of runs; seeded
src/perfrepair/data_handler/inbound/manifest.py : reads manifest.yaml; resolves a files key to a path
src/perfrepair/data_handler/inbound/probe_index.py : probe → engine types and the name each provider registers for a spelling
src/perfrepair/data_handler/inbound/results.py : benchmark.json + process files + prepared.yaml → PrimitiveRows and Summaries with runs per process; comparability notes
src/perfrepair/data_handler/inbound/run_log.py : skipped, unmeasured, not-runnable and measured records → deduplicated RunLog
src/perfrepair/data_handler/outbound/benchmark_runner.py : runs cryptobenchmark pipeline.py, with or without `--config`; returns the manifest path
src/perfrepair/data_handler/outbound/run_config.py : writes generated_perf_repair.yaml from a base global.yaml
src/perfrepair/dto/decision.py : OutboxRecord: one committed decision of any kind
src/perfrepair/dto/grouping.py : Family, Item, Profile; items.json and profiles.json documents; provider_of, algorithm_of
src/perfrepair/dto/grouping_output.py : Finding and checks.json
src/perfrepair/dto/grouping_state.py : Answer, Amendment, Group, Knowledge
src/perfrepair/dto/interop.py : PlannedPair, PairResult; interop_plan.yaml, the groups.json interop section, failed_pairs, pair_status, PAIR_STATUSES
src/perfrepair/dto/language.py : the language table: suffix, script suffix, statement terminators, template, comment nesting, `name: Type`
src/perfrepair/dto/manifest.py : BenchmarkManifest: the manifest.yaml contract with cryptobenchmark
src/perfrepair/dto/measurement.py : Summary and the Measurements document
src/perfrepair/dto/primitive.py : PrimitiveRow: one measured configuration, no numbers
src/perfrepair/dto/prompt.py : Prompt base and its lifetimes: SystemPrompt (run), TaskPrompt (session), CorrectionPrompt (turn); fingerprint
src/perfrepair/dto/report.py : report.json and summary.json vocabulary: step statuses, reported metrics and units, funnel stages, scoped case ids
src/perfrepair/dto/run_log.py : LogEntry, RunLog, statuses
src/perfrepair/dto/site.py : Scope, Dossier, Option (pins null = unknown), Estimate (pImprove null = n<2), Edit, Replacement; Option.interop (pair_status); NO_OPTION_REASONS, RISKS, DERIVED_RISKS (scope and option rows); the edit-kind table
src/perfrepair/dto/worthiness.py : MemberStats, PairMetrics, Configuration, GroupEvidence, Pair, Verdict, Verdicts
src/perfrepair/files.py : JSON and YAML read; atomic JSON write
src/perfrepair/run_dir.py : run directory: artifact names and loaders; AppPaths, the only definition of apps/<name>/ paths, cryptobenchmark's `measured/scoped/` files included
```
