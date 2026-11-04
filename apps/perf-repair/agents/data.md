# Data

## Calls
- `docs/artifacts.md` : every artifact: producer, consumers, validator

## Rules
- boundary: perf-repair reads cryptobenchmark only through `<device>/manifest.yaml` and the files it lists; that manifest must carry `deviceId`.
- run record: only `run_dir/run_record.py` writes `runs/run_<id>.json`, `<app>/finished.json` and `device.yaml` (`tests/test_run_record.py`).
- device stage: `device/` reruns a stage only when an input digest changed, its output is missing or the used set lacks rows (`docs/pipeline.md` Device stage, `docs/used-set.md`); `device.yaml` is written last and removed before any stage runs, so it never vouches for a half-made folder; `device/` never imports `app/`.
- dto: no I/O; every file-level document carries `schemaVersion`, one constant per artifact, and every read site refuses another through its `DocumentKind` (`dto/document.py`), declared beside the artifact's DTO, never a hand-written check (`run_dir.read_scopes`, `read_sites`, `read_edits`, `read_dossiers`: `schema_version`).
- numbers: summarised once in `inbound/results.py`; nothing downstream recomputes them.
- gate: the inbound command writes nothing until the manifest, rows, measurements and run log validate.
- names: every algorithm-name comparison goes through `catalog/names.py`; config's `AlgorithmNames.kt` reads the same file and must resolve `tests/fixtures/algorithm-names-cases.yaml` alike.
- names: a spelling goes in `catalog/algorithm-names.yaml` with a cited source; parameters (OAEP, MGF1, provider defaults) never do.
- names: the benchmark owns both name files (`apps/benchmark/modules/config/src/`); change them there and copy them here, `tests/test_names.py` fails until both match.
- names: a probe alias the catalog or another provider contradicts is `name_conflict` where it is used, never a pick.
- inputs: every setting is chosen by `inputs/resolve.py` from its `inputs/table.py` row; library code logs, only a `__main__` attaches a handler.
- bundled: a row in `catalog/bundled-providers.yaml` cites a source; its version is never there, it is the app's pin.
- screening: a row in `catalog/screening.yaml` cites a fetched source or says `source: unsourced`; its key is the canonical name.

## Workflow
- add an artifact: dto → name in `src/perfrepair/run_dir/layout.py` → validator (`agents/validation.md`) → row in `docs/artifacts.md`

## File structure

```
src/perfrepair/catalog/algorithm-names.yaml : canonical name ← spellings per engine type; key-size suffixes; transformation modes, paddings, per-algorithm synonyms; key formats
src/perfrepair/catalog/bundled-providers.yaml : data: per Gradle group:name an app ships, the provider it registers, create, alias, minSdk, notes, a known blocker, and its source
src/perfrepair/catalog/bundled_providers.py : the bundled-providers reader: every row's forms, keys and source checked, every problem at once; a row's providers.bundled entry at the app's pinned version; whether an app's registration expression builds the row's provider
src/perfrepair/catalog/names.py : the names reader: Canonical (name, keySize, known), engine types (what detection scans), fold, key formats, name_conflict, key_or_spelling (a conflict keys by its spelling)
src/perfrepair/catalog/screening.py : the screening reader: crypto, component, platform and future rules; every key canonical, statuses and sources checked; component match
src/perfrepair/catalog/screening.yaml : data: per (engine type, canonical name) a deprecated or accepted status with reason and source; Cipher base and mode rules; per-provider platform deprecation by targetSdk; draft future notes
src/perfrepair/child/__init__.py : docstring only
src/perfrepair/child/deadline.py : Deadline: kills a child's process group (started in its own session) when its seconds pass, `expired` set, or when its caller fails
src/perfrepair/child/env.py : child_env: the environment of every child process, ANTHROPIC_API_KEY and ANTHROPIC_AUTH_TOKEN withheld
src/perfrepair/data_handler/inbound/__main__.py : command: manifest → rows.json, measurements.json, run_log.json, through device/inbound.py
src/perfrepair/data_handler/inbound/bootstrap.py : median bootstrap that resamples processes, then blocks of runs; seeded
src/perfrepair/data_handler/inbound/energy.py : the invalid energy cases of each energy.json a manifest's files.energy lists (a path or one per process)
src/perfrepair/data_handler/inbound/manifest.py : reads manifest.yaml; resolves a files key to a path; display_units, the one reader of the units every view shows
src/perfrepair/data_handler/inbound/primitives.py : read_primitives: the reader of primitives.tsv
src/perfrepair/data_handler/inbound/probe/__init__.py : exports only `Probe`; the `_` modules are private to the package (`tests/test_layers.py`)
src/perfrepair/data_handler/inbound/probe/_index.py : probe → engine types and the name each provider registers for a spelling, a composed transformation in the spelling the provider declares
src/perfrepair/data_handler/inbound/probe/_names.py : the probe's aliases merged onto the catalog; contradictions recorded as conflicts
src/perfrepair/data_handler/inbound/probe/_probe.py : Probe: the probe file parsed once; index, names, attributes, class names and generator-kind views built on first use
src/perfrepair/data_handler/inbound/probe/_services.py : per-service lookups: the one walk of each provider's services (none without providers), declared attributes, class names, the key kind a generator makes
src/perfrepair/data_handler/inbound/results.py : benchmark.json + process files + prepared.yaml → PrimitiveRows and a Summary per registry metric with runs per process; the cases with no runs of a required metric, apart; comparability notes
src/perfrepair/data_handler/inbound/run_context.py : RunContext: the manifest read once; catalog, families, screening, probe and benchmark documents on first use; tests inject any piece
src/perfrepair/data_handler/inbound/run_log.py : skipped, unmeasured, not-runnable and measured records → deduplicated RunLog
src/perfrepair/data_handler/outbound/benchmark_runner.py : runs cryptobenchmark pipeline.py, with or without `--config`, extra flags passed on; returns the manifest path; the transcript appended to <device>/log/pipeline/<run id>.log; a failed run is one `pipeline_failed` through terminate (exit, last error line, the call's transcript line; the tail in the Halt); a call past timeouts.pipeline killed with its children, one `pipeline_timeout`; the child's environment from child_env; identify: `--identify`'s device id, input digests and harness digest; check_dependencies: scripts/dependencies.py, `missing_dependency` before the first spawn
src/perfrepair/device/__init__.py : docstring only
src/perfrepair/device/benchmark_coverage.py : CoverageFile, the one writer of log/details/benchmark_coverage.yaml: rewritten whole, validated, at each gate point, each point's delta count and the run's deltas held in memory; clear_coverage
src/perfrepair/device/bundled.py : the bundled step after the targets' detect: missing set, suggestions, bundled-suggestions.yaml validated before writing, its events, bundled_missing through terminate; the entries to apply; on a host nothing is applied and the line says why
src/perfrepair/device/bundled_config.py : the base's providers.bundled group:names; bundled-global.yaml, the base with the applied entries; the config a per-app harness builds
src/perfrepair/device/bundled_missing.py : the missing set: providers the targets ship or name at a not_on_device site, neither on the device nor in the base's providers.bundled
src/perfrepair/device/bundled_suggest.py : the missing set against the bundled-providers catalog: matched at the pinned version, blocked, or unmatched with a reason
src/perfrepair/device/coverage.py : grouping coverage computed from the active outbox: pending items (in used.json when present), not used ones, whether the saved files are current; noRerun's reader
src/perfrepair/device/delta.py : run_delta: the gaps and their anchors measured by the pipeline with the stored config into <device>/delta/results, the stored thermal baseline, the device id checked first; the setup checked on a probe first, then the fingerprint and per-case setups after measuring, anchors' drift by the noise rule, then the add-only merge; rerun_whole, only with onSetupMismatch rerun
src/perfrepair/device/delta_config.py : the delta's global.yaml and test set: the stored config's run block (narrowed: a partial-only delta's variants and passes), its test set's include replaced by the gap and anchor items, overrides kept; the whole-rerun config
src/perfrepair/device/delta_estimate.py : the cases a delta plans and their time, from the stored plan and the transcripts' took: lines; the line printed before it runs
src/perfrepair/device/delta_merge.py : merge_delta: add-only; an id already stored or unequal per-case sample counts refused; a partial case's missing metric filled beside its runs; new files beside the old, manifest.yaml renamed in last, so an interrupt leaves the benchmark whole; each added case tagged with its session; the lost cases it measured again added to retried
src/perfrepair/device/energy.py : after a device run: one energy_invalid per invalid energy case across its process files, its reasons as the detail; `energy_unreadable` when the files cannot be read; both through terminate
src/perfrepair/device/gate.py : benchmark_gate: measured_check at a gate point, coverage written; delta gaps measured once (onGap delta) or not_benchmarked (onGap stop, --device-results with the command); setup_mismatch, setup_drift lines; checked again, a gap left stops
src/perfrepair/device/gate_after.py : after a merge: inbound and primitives made again, device.yaml rewritten with the manifest, the primitives inputs and the measured set
src/perfrepair/device/inbound.py : the inbound stage: manifest → rows.json, measurements.json, run_log.json, validated before writing; a case with no runs of a required metric is no_required_metric through terminate (skip: left out, named in the run log)
src/perfrepair/device/measured_check.py : measured_check: per used item and planned case and metric, measured or a gap: never_planned, lost, partial (a metric or a variant), low_quality (fewer than MIN_RUNS, coded), repeats (the manifest's retried), refused (run log), no_operation (the manifest's operations); planned_set, the plan as the used set with device.filterByApps off
src/perfrepair/device/measures.py : perfMode owns run.metrics: what each harness can measure (the one table), the decided list, metrics-global.yaml, perf_mode_unmeasured for a required metric no harness row holds, perf_mode_maybe_unmeasured, run_metrics_overridden, the line saying what the run measures
src/perfrepair/device/missing_rows.py : the rows of primitives_missing.yaml, one function per place a primitive an app uses is found unavailable: its sites, the bundled step, the unscreened names, the run log, the other variant, the benchmark gate's coverage
src/perfrepair/device/plan.py : which device stage reruns and why: current digests against the manifest's `inputs` and device.yaml (primitives: the rows, measurements and screen.json digests it was made from); upstream reruns carry down; a forced reason (the used set); base_inputs: a used-set manifest's config digest mapped back to the base; --refresh reruns primitives
src/perfrepair/device/primitives.py : the primitives stage: rows, measurements, screen.json → primitives.tsv, validated as it reads back; its input digests; status_of (screen.json by qualified name); unusable: primitives.tsv absent or in another schema, rebuilt whatever its inputs
src/perfrepair/device/primitives_missing.py : MissingList, the one writer of log/details/primitives_missing.yaml: a run's rows per source, the file rewritten whole on each change, an empty list when the folder opens; the one pointer event; the pointer line the guide prints last
src/perfrepair/device/seen.py : seen(): what a device folder holds now (manifest, device.yaml, inbound files, grouping files, primitives.tsv) for the plan
src/perfrepair/device/selection.py : with device.filterByApps: what the last benchmark measured, why the benchmark reruns for it (only with no used-set record: a set that grew is the gate's), the exclude rules and used-global.yaml, device.yaml's benchmark section
src/perfrepair/device/selection_adds.py : the used set's includes: one rule per used runnable item in its declared spelling, written as used-testset.yaml beside the device folder; an empty include adds none
src/perfrepair/device/setup_fingerprint.py : fingerprint of a benchmark folder: device id, runtime (build fingerprint, compile mode), bundled providers with versions, process files, the run block and the plan's, the energy mark; before_measuring, what a probe can already tell; case_setups; differing, one line per field; without_narrowed, what a partial-only delta left out
src/perfrepair/device/stage.py : probe_device(): identify, the device folder's lock, the perfMode's measurement check, the pass, run the needed stages, write device.yaml last; `device <stage>: reused` or `ran: <reason>`
src/perfrepair/device/stage_pass.py : the pass of one probe_device call: the whole selection, or with detect: probe and screen first, the targets' detect, the bundled step, used.json, the benchmark of the measured set only, the used items added as includes; device.yaml dropped while a stage it vouches for reruns
src/perfrepair/device/stage_run.py : Run: one probe_device call's settings; the probe and the needed stages run (pipeline, inbound, grouping build, primitives), each with its event
src/perfrepair/device/used.py : the used step: each app's sites.json → the items its sites resolve to, their groups' members, an ungrouped one's candidates → used.json, validated before writing; clear_used
src/perfrepair/dto/benchmark_coverage.py : Gap, Coverage, the gap classes and their action (delta or coded), totals, items; benchmark_coverage.yaml (schema 1); the onGap and onSetupMismatch values
src/perfrepair/dto/bundled.py : device.bundled's values, BundledPolicy; MissingProvider, Coordinate, Suggestion, Suggestions: bundled-suggestions.yaml (schema 1); applied_entries, entries_digest
src/perfrepair/dto/change.py : PairDiff (input, key, output, reach), Change (class, diff, reject reasons); CHANGES in rank order, REJECT_REASONS, admits(maxChange, class)
src/perfrepair/dto/charter.py : charter.json (schema 1): the system and correction texts with each source, the schema, the inputs; read back to a Charter
src/perfrepair/dto/classify.py : Evidence (one unknown item as the classify model sees it), Batch (key: its ids), Answer, ANSWERS; batches.json document
src/perfrepair/dto/coded.py : CODE and code_in, the code word a failure message starts with; InputError, the one coded error a refused input raises (`.code`, `.path`, `.detail`)
src/perfrepair/dto/decision.py : OutboxRecord: one committed decision of any kind, the AgentIdentity (gateway, model, effort) that answered it, and the evidence digest when its kind declares one
src/perfrepair/dto/device.py : DeviceRecord: device.yaml (deviceId, mode, runtime summary, input digests, the manifest's sha256, primitives.tsv's input digests, the used-set benchmark: generated config digest, measured set digest and items)
src/perfrepair/dto/document.py : DocumentKind: a versioned document's accepted schemaVersion (one or several), its reader's refusal text and error type; check, the one schemaVersion check every reader calls
src/perfrepair/dto/dossier.py : Dossier, Option (pins null = unknown), Estimate (pImprove null = n<2), NoEstimate; Option.interop (pair_status), Option.screen (the app's status); NO_OPTION_REASONS in filter order and reason_code, pin_text; not_on_device_sites, a site list's missing names and which are absent
src/perfrepair/dto/event.py : Event: one events.jsonl line (schema 1); event names (a `finding`: a coded fact for the status log), kinds, each field's types
src/perfrepair/dto/grouping.py : Family, Item (key: what a record names), Profile (isolated: a generator of unknown key contract); key contract values, labels and sources; items.json and profiles.json (schema 5) documents; provider_of, algorithm_of
src/perfrepair/dto/grouping_output.py : Finding and checks.json
src/perfrepair/dto/grouping_state.py : Answer, Amendment, Group, Knowledge (open_groups: model-made only; retired: memberless groups a record still names); the `code_` id prefix
src/perfrepair/dto/interop.py : PlannedPair, PairResult; interop_plan.yaml with its notCheckable pairs, the groups.json interop section, failed_pairs, pair_status, PAIR_STATUSES
src/perfrepair/dto/lifecycle.py : Lifecycle, Step, Requirement, Settled: a primitive object from creation to last use; statuses, reasons, bindings, roles, origins, the open ones
src/perfrepair/dto/manifest.py : BenchmarkManifest: the manifest.yaml contract with cryptobenchmark, its display units and harness operations included
src/perfrepair/dto/measurement.py : Summary and the Measurements document
src/perfrepair/dto/metrics.py : the metric registry, the only metric list: benchmark.json name, unit, lowerIsBetter, energy kinds, perfMode keys, required, positive, the run.metrics or energy capture that measures it, its run.passes pass
src/perfrepair/dto/pattern.py : the two divergence categories (fixed, notFixed), the benchmark variants and the legacy one, each pattern reason with its category and rule words
src/perfrepair/dto/perf_mode.py : PerfMode: `generic`/`all` (every key, overall rule) or a list of keys parsed and named; the union across apps; the selected registry metrics, the required ones, the views timeNs is shown as; the no_evidence reason
src/perfrepair/dto/primitive.py : PrimitiveRow: one measured configuration, its benchmark variant and the delta session that measured it (with its drift), no numbers; rows.json schema
src/perfrepair/dto/primitives.py : PrimitiveLine, PrimitivesTable: primitives.tsv (schema 3, a variant column) as text both ways; a median column per (metric, input size), n and cv per metric; 4 significant digits
src/perfrepair/dto/primitives_missing.py : MissingRow, its merge; primitives_missing.yaml (schema 1): reasons (not_benchmarked: the gate's), actions, the document; pointer_line
src/perfrepair/dto/prompt.py : Prompt base and its lifetimes: SystemPrompt (run), TaskPrompt (session), CorrectionPrompt (turn); fingerprint, with the run inputs a kind adds; each prompt's source, never hashed
src/perfrepair/dto/replacement.py : Replacement, Edit, the edit-kind table; DECISIONS, RISKS, DERIVED_RISKS (scope and option rows) and required_risks; read_replacements
src/perfrepair/dto/report.py : report.json and summary.json vocabulary: of_pattern and pattern_counts (rows per category, never mixed); step statuses, reported metrics and units, has_views (the time metric throughput selects), funnel stages, the members a unit left staying, scoped case ids
src/perfrepair/dto/run_log.py : LogEntry, RunLog, statuses
src/perfrepair/dto/screen.py : Verdict (broken, platform_deprecated, unverified, accepted, unknown; reason, source, canonical, keySize); CODE_GROUPED, NEVER_TARGET; with_answer (model answer onto a verdict, `model:<fingerprint>`); RANK and lowers_status (the don't-lower-the-status rule); verdicts by qualified name; screen.json document (schema 4, with the catalog identity and the `built` items and profiles digests)
src/perfrepair/dto/shipped.py : Shipped: one app.json `bundled` entry (artifact, providerName, version); shipped, shipped_names: the one reader of what the app ships
src/perfrepair/dto/signature.py : Signature and its components, known, convention or unknown; decided, assumed, identity, differing
src/perfrepair/dto/site.py : Scope, scope_id; each app artifact's schema version; harness input sources and notMeasurable reasons
src/perfrepair/dto/types.py : TypeRow: an algorithm's output kind, Properties, Strength, minSdk and their sources
src/perfrepair/dto/unit.py : Link, Unit, Stay, PairInterop, UnitDossiers (one decision: a unit, its members' dossiers, the members that stay, inverse pairs' interop), unit_id, unit_entry, read_units, link kinds and their evidence
src/perfrepair/dto/units.py : DisplayUnits: the manifest's analysis.units (latency ms|us|ns, throughput MB/s|MiB/s|ops/s), parsed and checked, defaults mirroring :config; ns/op to each; significant-figure numbers
src/perfrepair/dto/used.py : UsedSet, UsedItem, AppUse: used.json (schema 1); via site, group or candidate; names_digest
src/perfrepair/dto/version.py : a Gradle version: pinned or not; newest of several
src/perfrepair/dto/worthiness.py : MemberStats (a Summary per selected metric), MetricComparison, PairMetrics (a comparison per selected metric), Configuration, GroupEvidence, Pair, Verdict, Verdicts
src/perfrepair/files.py : text, JSON and YAML read; read_versioned (a document refused unless its DocumentKind accepts it); atomic JSON write through a temp file of its own (mkstemp), fsync when durable; a text write that makes its parent folders; one-line append, a newline first after a cut line; read_jsonl, the one JSON-lines reader (whole lines, cut lines skipped, bad ones listed); several files staged then renamed in order; sha256 of a text or file
src/perfrepair/inputs/__init__.py : docstring only
src/perfrepair/inputs/check.py : Invalid and the checks a row or a gateway's settings class names
src/perfrepair/inputs/resolve.py : choose(): the first set candidate under its OnInvalid; unknown_key; resolve(): one input from its chain of candidates; Need, Resolved, InputError (`invalid`, `missing_file`, `missing_input`), a dto/coded.py InputError; a found default and a skipped optional input logged
src/perfrepair/inputs/table.py : every setting, one Row or RoleRow each (key, chain, check, default, OnInvalid; Need and packaged default for a file input); STOP_ROWS, one per overridable stop code, and the fixed codes known so setting one is not an unknown key; known_tree
src/perfrepair/log/__init__.py : exports attach, bug_log, command_run, emit, run_id, step
src/perfrepair/log/__main__.py : command: `summary <device> [--run ID | --last] [--json]`, the runs of events.jsonl, status lines last
src/perfrepair/log/attach.py : attach(): the stderr handler and the event sink a command installs, then the device folder it binds; command_run(): run_start and run_end of the outermost command; run_id(): the attached run's id; nested(), current_run()
src/perfrepair/log/emit.py : emit(): one event as a log record; step(): a timed start and end with counts and the digests of the files written; a step ended by a Halt records its code and `reported`
src/perfrepair/log/progress.py : Progress: the line watch prints per event; a running counter per model step (done/pending, rejected, cost, elapsed)
src/perfrepair/log/read.py : events.jsonl through read_jsonl, read whole or followed, whole lines only; `events_unreadable`
src/perfrepair/log/sink.py : EventSink: each perfrepair record as an Event line in events.jsonl, then its view lines; records before the folder is known kept in order; append_repaired and log_dropped, its own two notices; a data value JSON cannot write kept as text
src/perfrepair/log/status.py : the status view: one line per outcome (run header and end, app targets, device stages, guide stops, terminate's findings, errors, bugs), each starting with its code word, data.code before the detail's first word; a line already written by terminate is not repeated; a pointer finding is its detail; code_of and line, the one parser and formatter
src/perfrepair/log/stderr.py : the stderr handler: INFO and above, event records left out
src/perfrepair/log/summary.py : summarize(): the chosen runs per stage and per app folder: time, step durations, items, decisions, model calls, rejections, top problems, slowest items, tokens, cost; their status lines
src/perfrepair/log/summary_text.py : the summary as text lines, `status:` last
src/perfrepair/log/views.py : the views, each a function of one event: ai/<stage>.log per model stage (AI_LOGS: screening, classify, grouping, supervisor, worthiness, replace), bug.log, status.log; render() recomputes them
src/perfrepair/log/watch.py : watch(): polls events.jsonl, prints Progress lines, a counter rewritten in place on a terminal; exits after a run_end
src/perfrepair/run_dir/__init__.py : re-exports layout and read: the `run_dir` namespace every reader uses
src/perfrepair/run_dir/layout.py : device folder: artifact names (`.lock`, `runs/` included), finished devices of a root, worthiness-<perfMode> folders, the run log paths (log/: events, status, ai/<stage>, bug, pipeline/, details/primitives_missing.yaml, details/benchmark_coverage.yaml), used-testset.yaml, not_device_results, app folders; AppPaths and GroupingPaths, the only definitions of <app>/ and grouping/ paths, cryptobenchmark's `measured/scoped/` files included
src/perfrepair/run_dir/lock.py : DeviceLock: `<device>/.lock` by fcntl.flock, the holder's pid; another process is device_busy, the holding one takes it again
src/perfrepair/run_dir/read.py : artifact loaders: rows, measurements, run log, screen.json (load_screen, load_screen_catalog, load_screen_review; `built`, the digests screen.json binds to), load_used (None without used.json), read_scopes, read_sites, read_edits, read_dossiers (schema_version on another version, through read_versioned)
src/perfrepair/run_dir/run_record.py : RunRecord, the one writer of what a device folder says is done: runs/run_<id>.json (its id, onExisting, the facade's settings tree), each <app>/finished.json (is_done, app_done; cleared on an app's first rerun step with its report), device.yaml read, write and drop; runs/delta_asked.json, the last merged delta each app's replace asked after; the folder's lock held from open to close
src/perfrepair/stop/__init__.py : re-exports: CODES, the actions, Halt, code_of, terminate
src/perfrepair/stop/codes.py : the code table: every stop, warn and skip code once with its default action, the actions stops.<code> may choose (none: fixed, and why), exit and next step
src/perfrepair/stop/halt.py : Halt, the exception terminate raises after its event; Coded, the name its raisers import for dto/coded.py's InputError; code_of, the code a failure carries as `.code` or its message's first word
src/perfrepair/stop/policy.py : the stops reader the settings layer installs; a code's action, its default without one
src/perfrepair/stop/terminate.py : terminate(): the action resolved, one finding event with data.code, action and next (the code's, or next_step), then Halt, warn or skip
src/perfrepair/watch/__init__.py : docstring only
src/perfrepair/watch/__main__.py : command: `watch <device> [--from-start]`, log/watch.py on a device folder; Ctrl-C exits 130
```
