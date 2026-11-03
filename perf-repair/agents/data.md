# Data

## Calls
- `docs/artifacts.md` : every artifact: producer, consumers, validator

## Rules
- boundary: perf-repair reads cryptobenchmark only through `<device>/manifest.yaml` and the files it lists; that manifest must carry `deviceId`.
- device stage: `device/` reruns a stage only when an input digest changed or its output is missing (`docs/pipeline.md` Device stage); `device.yaml` is written last and removed before any stage runs, so it never vouches for a half-made folder; `device/` never imports `app/`.
- dto: no I/O; every file-level document carries `schemaVersion` and its reader refuses another.
- numbers: summarised once in `inbound/results.py`; nothing downstream recomputes them.
- gate: the inbound command writes nothing until the manifest, rows, measurements and run log validate.
- names: every algorithm-name comparison goes through `catalog/names.py`; config's `AlgorithmNames.kt` reads the same file and must resolve `tests/fixtures/algorithm-names-cases.yaml` alike.
- names: a spelling goes in `catalog/algorithm-names.yaml` with a cited source; parameters (OAEP, MGF1, provider defaults) never do.
- names: a probe alias the catalog or another provider contradicts is `name_conflict` where it is used, never a pick.
- inputs: every setting is chosen by `inputs/resolve.py` from its `inputs/table.py` row; library code logs, only a `__main__` attaches a handler.
- screening: a row in `catalog/screening.yaml` cites a fetched source or says `source: unsourced`; its key is the canonical name.

## Workflow
- add an artifact: dto → name in `src/perfrepair/run_dir.py` → validator (`agents/validation.md`) → row in `docs/artifacts.md`

## File structure

```
src/perfrepair/catalog/algorithm-names.yaml : canonical name ← spellings per engine type; key-size suffixes; transformation modes, paddings, per-algorithm synonyms; key formats
src/perfrepair/catalog/names.py : the names reader: Canonical (name, keySize, known), engine types (what detection scans), fold, key formats, name_conflict
src/perfrepair/catalog/screening.py : the screening reader: crypto, component, platform and future rules; every key canonical, statuses and sources checked; component match
src/perfrepair/catalog/screening.yaml : data: per (engine type, canonical name) a deprecated or accepted status with reason and source; Cipher base and mode rules; per-provider platform deprecation by targetSdk; draft future notes
src/perfrepair/data_handler/inbound/__main__.py : command: manifest → rows.json, measurements.json, run_log.json, through device/inbound.py
src/perfrepair/data_handler/inbound/bootstrap.py : median bootstrap that resamples processes, then blocks of runs; seeded
src/perfrepair/data_handler/inbound/manifest.py : reads manifest.yaml; resolves a files key to a path
src/perfrepair/data_handler/inbound/probe/__init__.py : exports only `Probe`; the `_` modules are private to the package (`tests/test_layers.py`)
src/perfrepair/data_handler/inbound/probe/_index.py : probe → engine types and the name each provider registers for a spelling
src/perfrepair/data_handler/inbound/probe/_names.py : the probe's aliases merged onto the catalog; contradictions recorded as conflicts
src/perfrepair/data_handler/inbound/probe/_probe.py : Probe: the probe file parsed once; index, names, attributes, class names and generator-kind views built on first use
src/perfrepair/data_handler/inbound/probe/_services.py : per-service lookups: declared attributes, class names, the key kind a generator makes
src/perfrepair/data_handler/inbound/results.py : benchmark.json + process files + prepared.yaml → PrimitiveRows and Summaries with runs per process; comparability notes
src/perfrepair/data_handler/inbound/run_context.py : RunContext: the manifest read once; catalog, families, screening, probe and benchmark documents on first use; tests inject any piece
src/perfrepair/data_handler/inbound/run_log.py : skipped, unmeasured, not-runnable and measured records → deduplicated RunLog
src/perfrepair/data_handler/outbound/benchmark_runner.py : runs cryptobenchmark pipeline.py, with or without `--config`, extra flags passed on; returns the manifest path; identify: `--identify`'s device id and input digests
src/perfrepair/data_handler/outbound/run_config.py : writes generated_perf_repair.yaml from a base global.yaml
src/perfrepair/device/__init__.py : docstring only
src/perfrepair/device/inbound.py : the inbound stage: manifest → rows.json, measurements.json, run_log.json, validated before writing
src/perfrepair/device/plan.py : which device stage reruns and why: current digests against the manifest's `inputs` and device.yaml; upstream reruns carry down
src/perfrepair/device/stage.py : probe_device(): identify, plan, run the needed stages (pipeline, inbound, grouping build), write device.yaml last; `device <stage>: reused` or `ran: <reason>`
src/perfrepair/dto/charter.py : charter.json (schema 1): the system and correction texts with each source, the schema, the inputs; read back to a Charter
src/perfrepair/dto/classify.py : Evidence (one unknown item as the classify model sees it), Batch (key: its ids), Answer, ANSWERS; batches.json document
src/perfrepair/dto/decision.py : OutboxRecord: one committed decision of any kind and the AgentIdentity (gateway, model, effort) that answered it
src/perfrepair/dto/device.py : DeviceRecord: device.yaml (deviceId, mode, runtime summary, input digests, the manifest's sha256)
src/perfrepair/dto/event.py : Event: one events.jsonl line (schema 1); event names, kinds, each field's types
src/perfrepair/dto/grouping.py : Family, Item (key: what a record names), Profile; key contract values and labels; items.json and profiles.json (schema 2) documents; provider_of, algorithm_of
src/perfrepair/dto/grouping_output.py : Finding and checks.json
src/perfrepair/dto/grouping_state.py : Answer, Amendment, Group, Knowledge (open_groups: model-made only; retired: memberless groups a record still names); the `code_` id prefix
src/perfrepair/dto/interop.py : PlannedPair, PairResult; interop_plan.yaml with its notCheckable pairs, the groups.json interop section, failed_pairs, pair_status, PAIR_STATUSES
src/perfrepair/dto/manifest.py : BenchmarkManifest: the manifest.yaml contract with cryptobenchmark
src/perfrepair/dto/measurement.py : Summary and the Measurements document
src/perfrepair/dto/primitive.py : PrimitiveRow: one measured configuration, no numbers
src/perfrepair/dto/prompt.py : Prompt base and its lifetimes: SystemPrompt (run), TaskPrompt (session), CorrectionPrompt (turn); fingerprint, with the run inputs a kind adds; each prompt's source, never hashed
src/perfrepair/dto/report.py : report.json and summary.json vocabulary: step statuses, reported metrics and units, funnel stages, scoped case ids
src/perfrepair/dto/run_log.py : LogEntry, RunLog, statuses
src/perfrepair/dto/screen.py : Verdict (broken, platform_deprecated, unverified, accepted, unknown; reason, source, canonical, keySize); CODE_GROUPED, NEVER_TARGET; with_answer (model answer onto a verdict, `model:<fingerprint>`); RANK and lowers_status (the don't-lower-the-status rule); verdicts by qualified name; screen.json document (schema 4, with the catalog identity and the `built` items and profiles digests)
src/perfrepair/dto/site.py : Scope, Dossier, Option (pins null = unknown), Estimate (pImprove null = n<2), Edit, Replacement; Option.interop (pair_status), Option.screen (the app's status); NO_OPTION_REASONS in filter order, RISKS, DERIVED_RISKS (scope and option rows); the edit-kind table
src/perfrepair/dto/worthiness.py : MemberStats, PairMetrics, Configuration, GroupEvidence, Pair, Verdict, Verdicts
src/perfrepair/files.py : JSON and YAML read; atomic JSON write; one-line append; several files staged then renamed in order; sha256 of a text or file
src/perfrepair/inputs/__init__.py : docstring only
src/perfrepair/inputs/check.py : Invalid and the checks a row or a gateway's settings class names
src/perfrepair/inputs/resolve.py : choose(): the first set candidate under its OnInvalid; unknown_key; resolve(): one input from its chain of candidates; Need, Resolved, InputError (`invalid`, `missing_file`, `missing_input`); a found default and a skipped optional input logged
src/perfrepair/inputs/table.py : every setting, one Row or RoleRow each (key, chain, check, default, OnInvalid; Need and packaged default for a file input); known_tree
src/perfrepair/log/__init__.py : exports attach, bug_log, command_run, emit, step
src/perfrepair/log/__main__.py : command: `summary <device> [--run ID] [--json]`, one run of events.jsonl
src/perfrepair/log/attach.py : attach(): the stderr handler and the event sink a command installs, then the device folder it binds; command_run(): run_start and run_end of the outermost command
src/perfrepair/log/emit.py : emit(): one event as a log record; step(): a timed start and end with counts and the digests of the files written
src/perfrepair/log/progress.py : Progress: the line watch prints per event; a running counter per model step (done/pending, rejected, cost, elapsed)
src/perfrepair/log/read.py : events.jsonl read whole or followed, whole lines only; `events_unreadable`
src/perfrepair/log/sink.py : EventSink: each perfrepair record as an Event line in events.jsonl, then its view lines; records before the folder is known kept in order
src/perfrepair/log/stderr.py : the stderr handler: INFO and above, event records left out
src/perfrepair/log/summary.py : summarize(): one run per stage and per app folder: time, step durations, items, decisions, model calls, rejections, top problems, slowest items, tokens, cost
src/perfrepair/log/summary_text.py : the summary as text lines
src/perfrepair/log/views.py : the views screening/ai.log, grouping/ai.log, bug.log, each a function of one event; render() recomputes them
src/perfrepair/log/watch.py : watch(): polls events.jsonl, prints Progress lines, a counter rewritten in place on a terminal; exits after a run_end
src/perfrepair/run_dir.py : device folder: finished devices of a root, the run log paths (log/), not_device_results, app folders, device.yaml read and write, artifact names and loaders (screen.json: load_screen, load_screen_catalog, load_screen_review; `built`, the digests screen.json binds to); AppPaths and GroupingPaths, the only definitions of <app>/ and grouping/ paths, cryptobenchmark's `measured/scoped/` files included
src/perfrepair/watch/__init__.py : docstring only
src/perfrepair/watch/__main__.py : command: `watch <device> [--from-start]`, log/watch.py on a device folder; Ctrl-C exits 130
```
