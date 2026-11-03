# Data

## Calls
- `docs/artifacts.md` : every artifact: producer, consumers, validator

## Rules
- boundary: perf-repair reads cryptobenchmark only through `<device>/manifest.yaml` and the files it lists; that manifest must carry `deviceId`.
- device stage: `device/` reruns a stage only when an input digest changed, its output is missing or the used set lacks rows (`docs/pipeline.md` Device stage, `docs/used-set.md`); `device.yaml` is written last and removed before any stage runs, so it never vouches for a half-made folder; `device/` never imports `app/`.
- dto: no I/O; every file-level document carries `schemaVersion` and its reader refuses another.
- numbers: summarised once in `inbound/results.py`; nothing downstream recomputes them.
- gate: the inbound command writes nothing until the manifest, rows, measurements and run log validate.
- names: every algorithm-name comparison goes through `catalog/names.py`; config's `AlgorithmNames.kt` reads the same file and must resolve `tests/fixtures/algorithm-names-cases.yaml` alike.
- names: a spelling goes in `catalog/algorithm-names.yaml` with a cited source; parameters (OAEP, MGF1, provider defaults) never do.
- names: a probe alias the catalog or another provider contradicts is `name_conflict` where it is used, never a pick.
- inputs: every setting is chosen by `inputs/resolve.py` from its `inputs/table.py` row; library code logs, only a `__main__` attaches a handler.
- bundled: a row in `catalog/bundled-providers.yaml` cites a source; its version is never there, it is the app's pin.
- screening: a row in `catalog/screening.yaml` cites a fetched source or says `source: unsourced`; its key is the canonical name.

## Workflow
- add an artifact: dto → name in `src/perfrepair/run_dir.py` → validator (`agents/validation.md`) → row in `docs/artifacts.md`

## File structure

```
src/perfrepair/catalog/algorithm-names.yaml : canonical name ← spellings per engine type; key-size suffixes; transformation modes, paddings, per-algorithm synonyms; key formats
src/perfrepair/catalog/bundled-providers.yaml : data: per Gradle group:name an app ships, the provider it registers, create, alias, minSdk, notes, a known blocker, and its source
src/perfrepair/catalog/bundled_providers.py : the bundled-providers reader: every row's forms, keys and source checked, every problem at once; a row's providers.bundled entry at the app's pinned version
src/perfrepair/catalog/names.py : the names reader: Canonical (name, keySize, known), engine types (what detection scans), fold, key formats, name_conflict, key_or_spelling (a conflict keys by its spelling)
src/perfrepair/catalog/screening.py : the screening reader: crypto, component, platform and future rules; every key canonical, statuses and sources checked; component match
src/perfrepair/catalog/screening.yaml : data: per (engine type, canonical name) a deprecated or accepted status with reason and source; Cipher base and mode rules; per-provider platform deprecation by targetSdk; draft future notes
src/perfrepair/data_handler/inbound/__main__.py : command: manifest → rows.json, measurements.json, run_log.json, through device/inbound.py
src/perfrepair/data_handler/inbound/bootstrap.py : median bootstrap that resamples processes, then blocks of runs; seeded
src/perfrepair/data_handler/inbound/energy.py : the invalid energy cases of each energy.json a manifest's files.energy lists (a path or one per process)
src/perfrepair/data_handler/inbound/manifest.py : reads manifest.yaml; resolves a files key to a path; display_units, the one reader of the units every view shows
src/perfrepair/data_handler/inbound/primitives.py : read_primitives: the reader of primitives.tsv
src/perfrepair/data_handler/inbound/probe/__init__.py : exports only `Probe`; the `_` modules are private to the package (`tests/test_layers.py`)
src/perfrepair/data_handler/inbound/probe/_index.py : probe → engine types and the name each provider registers for a spelling
src/perfrepair/data_handler/inbound/probe/_names.py : the probe's aliases merged onto the catalog; contradictions recorded as conflicts
src/perfrepair/data_handler/inbound/probe/_probe.py : Probe: the probe file parsed once; index, names, attributes, class names and generator-kind views built on first use
src/perfrepair/data_handler/inbound/probe/_services.py : per-service lookups: declared attributes, class names, the key kind a generator makes
src/perfrepair/data_handler/inbound/results.py : benchmark.json + process files + prepared.yaml → PrimitiveRows and a Summary per registry metric with runs per process; comparability notes
src/perfrepair/data_handler/inbound/run_context.py : RunContext: the manifest read once; catalog, families, screening, probe and benchmark documents on first use; tests inject any piece
src/perfrepair/data_handler/inbound/run_log.py : skipped, unmeasured, not-runnable and measured records → deduplicated RunLog
src/perfrepair/data_handler/outbound/benchmark_runner.py : runs cryptobenchmark pipeline.py, with or without `--config`, extra flags passed on; returns the manifest path; the transcript appended to <device>/log/pipeline/<run id>.log; a failed run is one `pipeline_failed` finding (exit, last error line, the call's transcript line); identify: `--identify`'s device id and input digests
src/perfrepair/data_handler/outbound/run_config.py : writes generated_perf_repair.yaml from a base global.yaml
src/perfrepair/device/__init__.py : docstring only
src/perfrepair/device/bundled.py : the bundled step after the targets' detect: missing set, suggestions, bundled-suggestions.yaml validated before writing, its events, the warn-or-stop; the entries to apply
src/perfrepair/device/bundled_config.py : the base's providers.bundled group:names; bundled-global.yaml, the base with the applied entries; the config a per-app harness builds
src/perfrepair/device/bundled_missing.py : the missing set: providers the targets ship or name at a not_on_device site, neither on the device nor in the base's providers.bundled
src/perfrepair/device/bundled_policy.py : the one warn-or-stop decision for a coded device finding: one event, outcome stop or warn, data {code, items}; DeviceHalt
src/perfrepair/device/bundled_suggest.py : the missing set against the bundled-providers catalog: matched at the pinned version, blocked, or unmatched with a reason
src/perfrepair/device/coverage.py : grouping coverage computed from the active outbox: pending items (in used.json when present), not used ones, whether the saved files are current; noRerun's reader
src/perfrepair/device/energy.py : after a device run: one `finding` event per invalid energy case across its process files, keyed by its first reason; `energy_unreadable` when the files cannot be read
src/perfrepair/device/inbound.py : the inbound stage: manifest → rows.json, measurements.json, run_log.json, validated before writing
src/perfrepair/device/measures.py : the run config's measurements (run.metrics, run-level energy capture) against the perfMode: a selected run.metrics switch missing stops (perf_mode_unmeasured), run-level energy missing is a `perf_mode_unmeasured` finding, unselected measurements are logged
src/perfrepair/device/plan.py : which device stage reruns and why: current digests against the manifest's `inputs` and device.yaml (primitives: the rows, measurements and screen.json digests it was made from); upstream reruns carry down; a forced reason (the used set); base_inputs: a used-set manifest's config digest mapped back to the base; --refresh reruns primitives
src/perfrepair/device/primitives.py : the primitives stage: rows, measurements, screen.json → primitives.tsv, validated as it reads back; its input digests; status_of (screen.json by qualified name)
src/perfrepair/device/selection.py : with device.filterByApps: what the last benchmark measured, why the used set reruns it, the exclude rules and used-global.yaml, device.yaml's benchmark section
src/perfrepair/device/stage.py : probe_device(): identify, the perfMode's measurement check, plan, run the needed stages (pipeline, inbound, grouping build, primitives), write device.yaml last; with detect: probe and screen first, the targets' detect, used.json, the benchmark of the measured set only; `device <stage>: reused` or `ran: <reason>`
src/perfrepair/device/used.py : the used step: each app's sites.json → the items its sites resolve to, their groups' members, an ungrouped one's candidates → used.json, validated before writing; clear_used
src/perfrepair/dto/bundled.py : device.bundled's values, BundledPolicy; MissingProvider, Coordinate, Suggestion, Suggestions: bundled-suggestions.yaml (schema 1); applied_entries, entries_digest
src/perfrepair/dto/charter.py : charter.json (schema 1): the system and correction texts with each source, the schema, the inputs; read back to a Charter
src/perfrepair/dto/classify.py : Evidence (one unknown item as the classify model sees it), Batch (key: its ids), Answer, ANSWERS; batches.json document
src/perfrepair/dto/decision.py : OutboxRecord: one committed decision of any kind, the AgentIdentity (gateway, model, effort) that answered it, and the evidence digest when its kind declares one
src/perfrepair/dto/device.py : DeviceRecord: device.yaml (deviceId, mode, runtime summary, input digests, the manifest's sha256, primitives.tsv's input digests, the used-set benchmark: generated config digest, measured set digest and items)
src/perfrepair/dto/event.py : Event: one events.jsonl line (schema 1); event names (a `finding`: a coded fact for the status log), kinds, each field's types
src/perfrepair/dto/grouping.py : Family, Item (key: what a record names), Profile; key contract values and labels; items.json and profiles.json (schema 4) documents; provider_of, algorithm_of
src/perfrepair/dto/grouping_output.py : Finding and checks.json
src/perfrepair/dto/grouping_state.py : Answer, Amendment, Group, Knowledge (open_groups: model-made only; retired: memberless groups a record still names); the `code_` id prefix
src/perfrepair/dto/interop.py : PlannedPair, PairResult; interop_plan.yaml with its notCheckable pairs, the groups.json interop section, failed_pairs, pair_status, PAIR_STATUSES
src/perfrepair/dto/lifecycle.py : Lifecycle, Step, Requirement, Settled: a primitive object from creation to last use; statuses, reasons, bindings, roles, origins, the open ones
src/perfrepair/dto/manifest.py : BenchmarkManifest: the manifest.yaml contract with cryptobenchmark, its display units included
src/perfrepair/dto/measurement.py : Summary and the Measurements document
src/perfrepair/dto/metrics.py : the metric registry, the only metric list: benchmark.json name, unit, lowerIsBetter, energy kinds, perfMode keys, required, positive, the run.metrics or energy capture that measures it
src/perfrepair/dto/perf_mode.py : PerfMode: generic or a list of keys parsed and named; the selected registry metrics, the required ones, the views timeNs is shown as; the no_evidence reason
src/perfrepair/dto/primitive.py : PrimitiveRow: one measured configuration, no numbers
src/perfrepair/dto/primitives.py : PrimitiveLine, PrimitivesTable: primitives.tsv (schema 1) as text both ways; a median column per (metric, input size), n, cv per metric; 4 significant digits
src/perfrepair/dto/prompt.py : Prompt base and its lifetimes: SystemPrompt (run), TaskPrompt (session), CorrectionPrompt (turn); fingerprint, with the run inputs a kind adds; each prompt's source, never hashed
src/perfrepair/dto/report.py : report.json and summary.json vocabulary: step statuses, reported metrics and units, has_views (the time metric throughput selects), funnel stages, the members a unit left staying, scoped case ids
src/perfrepair/dto/run_log.py : LogEntry, RunLog, statuses
src/perfrepair/dto/screen.py : Verdict (broken, platform_deprecated, unverified, accepted, unknown; reason, source, canonical, keySize); CODE_GROUPED, NEVER_TARGET; with_answer (model answer onto a verdict, `model:<fingerprint>`); RANK and lowers_status (the don't-lower-the-status rule); verdicts by qualified name; screen.json document (schema 4, with the catalog identity and the `built` items and profiles digests)
src/perfrepair/dto/signature.py : Signature and its components, known, convention or unknown; decided, assumed, identity, differing
src/perfrepair/dto/site.py : Scope, Dossier, Option (pins null = unknown), Estimate (pImprove null = n<2), Edit, Replacement; Option.interop (pair_status), Option.screen (the app's status); NO_OPTION_REASONS in filter order and reason_code, RISKS, DERIVED_RISKS (scope and option rows); the edit-kind table
src/perfrepair/dto/unit.py : Link, Unit, Stay, PairInterop, UnitDossiers (one decision: a unit, its members' dossiers, the members that stay, inverse pairs' interop), unit_id, unit_entry, read_units, link kinds and their evidence
src/perfrepair/dto/units.py : DisplayUnits: the manifest's analysis.units (latency ms|us|ns, throughput MB/s|MiB/s|ops/s), parsed and checked, defaults mirroring :config; ns/op to each; significant-figure numbers
src/perfrepair/dto/used.py : UsedSet, UsedItem, AppUse: used.json (schema 1); via site, group or candidate; names_digest
src/perfrepair/dto/version.py : a Gradle version: pinned or not; newest of several
src/perfrepair/dto/worthiness.py : MemberStats (a Summary per selected metric), MetricComparison, PairMetrics (a comparison per selected metric), Configuration, GroupEvidence, Pair, Verdict, Verdicts
src/perfrepair/files.py : text, JSON and YAML read; atomic JSON write; one-line append; several files staged then renamed in order; sha256 of a text or file
src/perfrepair/inputs/__init__.py : docstring only
src/perfrepair/inputs/check.py : Invalid and the checks a row or a gateway's settings class names
src/perfrepair/inputs/resolve.py : choose(): the first set candidate under its OnInvalid; unknown_key; resolve(): one input from its chain of candidates; Need, Resolved, InputError (`invalid`, `missing_file`, `missing_input`); a found default and a skipped optional input logged
src/perfrepair/inputs/table.py : every setting, one Row or RoleRow each (key, chain, check, default, OnInvalid; Need and packaged default for a file input); known_tree
src/perfrepair/log/__init__.py : exports attach, bug_log, command_run, emit, run_id, step
src/perfrepair/log/__main__.py : command: `summary <device> [--run ID | --last] [--json]`, the runs of events.jsonl, status lines last
src/perfrepair/log/attach.py : attach(): the stderr handler and the event sink a command installs, then the device folder it binds; command_run(): run_start and run_end of the outermost command; run_id(): the attached run's id
src/perfrepair/log/emit.py : emit(): one event as a log record; step(): a timed start and end with counts and the digests of the files written
src/perfrepair/log/progress.py : Progress: the line watch prints per event; a running counter per model step (done/pending, rejected, cost, elapsed)
src/perfrepair/log/read.py : events.jsonl read whole or followed, whole lines only; `events_unreadable`
src/perfrepair/log/sink.py : EventSink: each perfrepair record as an Event line in events.jsonl, then its view lines; records before the folder is known kept in order
src/perfrepair/log/status.py : the status view: one line per outcome (run header and end, app targets, device stages, guide stops, findings, errors, bugs), each starting with its code word; code_of and line, the one parser and formatter
src/perfrepair/log/stderr.py : the stderr handler: INFO and above, event records left out
src/perfrepair/log/summary.py : summarize(): the chosen runs per stage and per app folder: time, step durations, items, decisions, model calls, rejections, top problems, slowest items, tokens, cost; their status lines
src/perfrepair/log/summary_text.py : the summary as text lines, `status:` last
src/perfrepair/log/views.py : the views, each a function of one event: ai/<stage>.log per model stage (AI_LOGS: screening, classify, grouping, supervisor, worthiness, replace), bug.log, status.log; render() recomputes them
src/perfrepair/log/watch.py : watch(): polls events.jsonl, prints Progress lines, a counter rewritten in place on a terminal; exits after a run_end
src/perfrepair/run_dir.py : device folder: finished devices of a root, worthiness-<perfMode> folders, the run log paths (log/: events, status, ai/<stage>, bug, pipeline/), not_device_results, app folders, device.yaml read and write, load_used (None without used.json), artifact names and loaders (screen.json: load_screen, load_screen_catalog, load_screen_review; `built`, the digests screen.json binds to); AppPaths and GroupingPaths, the only definitions of <app>/ and grouping/ paths, cryptobenchmark's `measured/scoped/` files included
src/perfrepair/watch/__init__.py : docstring only
src/perfrepair/watch/__main__.py : command: `watch <device> [--from-start]`, log/watch.py on a device folder; Ctrl-C exits 130
```
