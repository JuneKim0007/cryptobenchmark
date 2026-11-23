# lib/cryptobench

The Python library of `apps/benchmark-runner` and `apps/perf-repair`: `shared/` (the readers of the implementation guide under `algorithms/`, paths, documents, device mechanics, results, settings), `pipeline/` (the stage framework) and `stages/` (one package per stage). Data never lives here; readers never live in `algorithms/`.

```
../../algorithms/ : data: `<family>_catalogue.yaml` per family, one entry per id `<type>|<canonical>` (key, required, optional, conditions, lifecycle, operations, contract, sourcedOnly, providers, provenance); `common.yaml` sources, keyStrength maps, deterministicRelied; `recipes.yaml` how each parameter object a row names is made; `deviations.yaml` facts shared by a set of names and builds, stated once;
../../algorithms/algorithm-names.yaml : canonical name ← spellings per engine type; key-size suffixes; transformation modes, paddings, per-algorithm synonyms; key formats
../../algorithms/engine-operations.yaml : data: per JCA engine type the operations the harness times; read by preparation EngineTypes and copied into each manifest's operations
../../algorithms/families.yaml : predefined families with fixed descriptions, the one copy
../../algorithms/glossary.yaml : data: one defined meaning per key and value of groups.yaml, the catalogues, recipes.yaml, deviations.yaml, provider-builds.yaml and algorithm-names.yaml, a tree with sections group, algorithm, recipe, plan, deviation, build and names
../../algorithms/groups.yaml : data: per family its exemplars and the listed algorithm ids, from whose catalogue contracts the contract rows come; a person adds ids from group-candidates.yaml
../../algorithms/interchange.yaml : data: per engine type the components that split a group, the rules that read them from a canonical name, what a missing key contract means, and which contract each component states
../../algorithms/provider-builds.yaml : data: every provider build the catalogues' measured facts ran on, keyed <name> @ <build>, with what each says of itself; a behaviour true of a provider and the ids it reaches
../../algorithms/setup-catalog.yaml : data: per JCA engine type the paths it applies, the key it generates, what a fixed call still does per call; read by config and preparation
../../algorithms/vectors/ : known answers by family
cryptobench/__init__.py : package of the Python library the benchmark runner and perf-repair share
cryptobench/pipeline/__init__.py : package of the run's stage framework, importing no stage
cryptobench/pipeline/orchestrator/__init__.py : package of the session orchestrator: plan, workers, status lines, summary; imports no stage
cryptobench/pipeline/orchestrator/board.py : StatusBoard: one status line per target, redrawn in place on a terminal, else printed on change
cryptobench/pipeline/orchestrator/index.py : index.yaml: every case of a session's runs from the files each run wrote: suite, device, target, configured, prepared, skip code, runs measured, from
cryptobench/pipeline/orchestrator/plan.py : a session's plan before anything runs: devices listed, targets resolved and grouped, skips and notices; --check-session
cryptobench/pipeline/orchestrator/run.py : --session: the plan, order groups ascending, one worker per target and suite (sequential) with the session's discovery keys, each skip or failure in the session log, the target log and the summary, then index.yaml; a stop forwarded to the running worker; session_incomplete
cryptobench/pipeline/orchestrator/suite_config.py : one suite's global.yaml in the session folder: the target's config with selection.testSet the suite
cryptobench/pipeline/orchestrator/summary.py : Row; the summary table (target, suite, state, code, results), written as summary.txt
cryptobench/pipeline/orchestrator/tests/ : pytest tests of the orchestrator with fake workers: order, serials, skips, failures, stop, status lines
cryptobench/pipeline/orchestrator/worker.py : Worker: one pipeline.py child in its own process group, its transcript in the target log, ANDROID_SERIAL its target's; a stop goes through shared/stop/child.py with the pipeline grace; Outcome from its last error: and results: lines
cryptobench/pipeline/stage.py : StageContext (options, configuration, device, the parse-only check's answer, the --per-suite suite, the run's problems list), what each stage reads; Stage, a stage's shape
cryptobench/pipeline/took.py : the took: line of a timed step
cryptobench/shared/__init__.py : package of the components the stages share, importing neither the pipeline nor a stage
cryptobench/shared/catalogue/__init__.py : package of the implementation guide's readers
cryptobench/shared/catalogue/algorithms.py : reader of the catalogues, checked whole: entry fields, sources, contracts, type facts, provider overrides, linkage to the names file (canonical ids, key types, contract digests); lookup by family and id
cryptobench/shared/catalogue/deviations.py : reads algorithms/deviations.yaml, every word a glossary term; what an entry's providers holds once provider behaviours and deviations apply
cryptobench/shared/catalogue/families.py : the family catalog and (engine type, key kind) → family
cryptobench/shared/catalogue/glossary.py : what_is: a term, a subtree or one value's meaning of glossary.yaml; term_problems: an entry's words checked against it
cryptobench/shared/catalogue/grouping.py : Family, Item (key: what a record names), Profile (isolated: a generator of unknown key contract); key contract values, labels and sources; items.json (schema 1) and profiles.json (schema 5) documents; provider_of, algorithm_of
cryptobench/shared/catalogue/groups.py : reader of groups.yaml, checked whole: one group per family by id, contract rows from each member's catalogue contract, a row at each key contract
cryptobench/shared/catalogue/guide_items.py : guide_items: what the guide says for one effective.yaml's items at this device's builds
cryptobench/shared/catalogue/interchange.py : reader of interchange.yaml: engines, rules by canonical name; a component outside its splits is refused
cryptobench/shared/catalogue/key_types.py : a spelling's catalogue entry; its key.type as every build of a provider gives it, none when they differ; two key types compared through the names file's keyTypes
cryptobench/shared/catalogue/names.py : the names reader: Canonical (name, keySize, known), engine types (what detection scans), fold, same_engine, key formats, key types, linkage refusals (sized and named, OID. split), name_conflict, key_or_spelling (a conflict keys by its spelling)
cryptobench/shared/catalogue/overrides.py : a provider override's path in an entry, and one build's differences applied to a copy
cryptobench/shared/catalogue/provider_builds.py : reads provider-builds.yaml, registered ids canonical; a build key from what a probe records; a name resolves to one key or is provider_build_unknown
cryptobench/shared/catalogue/recipes.py : reads recipes.yaml, checked whole: one form per recipe, every word and each role's make and lives against the glossary, typed arguments, nested recipes present; the roles a recipe passes
cryptobench/shared/catalogue/reinit.py : whether init runs before every use of an operation, from one build's view of an entry
cryptobench/shared/catalogue/signature.py : Signature and its components, known, convention or unknown; decided, assumed, identity, differing
cryptobench/shared/catalogue/types.py : TypeRow: an algorithm's output kind, Properties, Strength, minSdk and their sources
cryptobench/shared/catalogue/vectors.py : known answers: read and checked whole, user vectors matched to cases by name, filled per provider for one run, --check's coverage lines
cryptobench/shared/catalogue/views.py : what an agent is shown: one entry with only its provider build's overrides (view_for), the groups' ids, descriptions and exemplars (list_groups), one group's members a page at a time (get_group)
cryptobench/shared/document/__init__.py : package of the YAML document reader and writer and the JSON document writer
cryptobench/shared/document/append.py : append_line, one whole line appended, a newline first after a line a crash cut
cryptobench/shared/document/document.py : parse_yaml, a YAML text as its one shape (a mapping unless named) or invalid_yaml at its line and column; DocumentKind: a versioned document's accepted schemaVersion and its reader's error type; check, the one schemaVersion check every reader calls, worded as Kotlin's SchemaVersion: missing_field: <name>: schemaVersion, unsupported_schema_version: <name>: <v>, this build reads <n> (<name> the path's file name, else the kind's name)
cryptobench/shared/document/dump.py : dump_yaml, a value as YAML text through one named profile (BLOCK, FLOW_LEAVES, WIDE, UNICODE, WIDE_UNICODE), each the option set its writers have always written
cryptobench/shared/document/json_dump.py : json_text, a document as JSON text (indent 1); write_json, that text through write_text
cryptobench/shared/document/write.py : write_text, a file replaced whole through a temporary of its writer's own (mode as a plain open gives, fsync and folder fsync when durable, exclusive refuses an existing file); Staging, the temporary's name, mode and fsync per writer (STAGED, MANIFEST); write_texts, several files staged then renamed in order
cryptobench/shared/device/__init__.py : package of the host's device steps, importing no app
cryptobench/shared/device/adb.py : the adb transport of a --device run: require_adb, connect, identity by getprop, the boot id, install, instrument and its OK line and report, push, pull, force-stop; a lost transport as DeviceLost, adb get-state
cryptobench/shared/device/aliases.py : the user's devices.yaml: alias to device key, one alias per key; no file is no aliases
cryptobench/shared/device/capture.py : a capture's runtime block, its schema version checked; the guide's platform name for it
cryptobench/shared/device/clocks.py : per-core cpufreq over adb; clocks.yaml and cpuLocked
cryptobench/shared/device/gradle_runner.py : runs one command of apps/benchmark/cli by its main class; filters its failure to the tool's own lines
cryptobench/shared/device/identity.py : device id from a capture's runtime block
cryptobench/shared/device/instrumentation.py : Instrumented, one instrumentation step's row (test class, clears before or after, pass rule, pulls); once() runs it, Failed when it did not pass; run() waits out a lost transport and runs it again
cryptobench/shared/device/plan.py : the device plan: pushed and AOT-compiled, prepared and skipped pulled back, the skips recorded so far, per-run outputs cleared; a run's push with the suppressErrors warning, then the energy pre-flight's files
cryptobench/shared/device/probe.py : DeviceRow; adb transports classified ready or not with a coded fix, keyed by ro.serialno or emulator:<avd>, unstable_id otherwise; the --devices listing
cryptobench/shared/device/reconnect.py : a lost adb transport: the bounded wait polling adb get-state, the step or case again, DeviceGone past the bound; Off for no wait
cryptobench/shared/device/tests/ : pytest tests of the device listing and the alias file, from hand-written adb and getprop text
cryptobench/shared/device/timeouts.py : ceilings of the host's subprocess steps (adb, install, instrument, case, gradle, compile, energy, analysis); expiry is one coded error
cryptobench/shared/digest/__init__.py : package of the digests over bytes
cryptobench/shared/digest/tree.py : byte_digest, the sha256 of some bytes; file_digest, of a file's bytes, None when absent; tree_digest, one digest of files in a given order, each its path under a root and its byte digest; globbed, the files glob patterns match but desktop litter and the patterns matching none; digest_of, their tree digest, a pattern matching none refused with the caller's error
cryptobench/shared/errors/__init__.py : package of the coded errors, importing nothing from the repo
cryptobench/shared/errors/coded.py : CODE and code_in, the code word a failure message starts with; code_of, the code a failure carries as `.code`; Coded, the marker of a failure whose message is its coded line (adds no ValueError base)
cryptobench/shared/errors/failures.py : AgentFailed (a provider's one coded failure line), GateError (the app gate's coded reasons), BenchmarkRunError (a pipeline.py run that failed), each on its own base; EnergyError (an energy source failed); AllSkipped (every case of a process a coded preparation skip, the run's outcome); CommandError (the runner's library code ends the run, its entry point prints the line)
cryptobench/shared/errors/codes.yaml : the glossary: every code once with its kind, its default action where a reader resolves it, an alias setting's values, perf-repair's stops.<code> entry
cryptobench/shared/errors/glossary.py : codes.yaml read through importlib.resources; Code: one code's default action, the actions stops.<code> may choose (none: fixed, and why), exit and next step; the action stop
cryptobench/shared/errors/halt.py : Halt, the exception terminate raises after its event
cryptobench/shared/errors/input_error.py : InputError, the one coded error a refused input raises (`.code`, `.path`, `.detail`)
cryptobench/shared/errors/line.py : one_line, a failure as one line of at most limit characters (500 unless given)
cryptobench/shared/errors/policy.py : the stops reader the settings layer installs; a code's action, its default without one; resolve, an alias setting's value to its code's action
cryptobench/shared/errors/validation.py : ValidationFailed, code artifact_invalid, and require: the stage gate
cryptobench/shared/log/__init__.py : package of the event log library code writes through, and the handlers a command attaches
cryptobench/shared/log/attach.py : attach(root, views): the stderr handler and the event sink a command installs on its root logger (the sink on cryptobench.event too), then the device folder it binds; command_run(): run_start and run_end of the outermost command; run_id(): the attached run's id; bug_log(), nested(), current_run()
cryptobench/shared/log/emit.py : emit(): one event as a log record (logger cryptobench.event, attribute cryptobench_event); step(): a timed start and end with counts and the digests of the files written; a step ended by a Halt records its code and `reported`; elapsed_ms
cryptobench/shared/log/event.py : Event: one events.jsonl line (schema 1); event names (a `finding`: a coded fact for the status log), kinds, each field's types
cryptobench/shared/log/sink.py : EventSink(views): each record under the root logger as an Event line in events.jsonl, then each view's line; records before the folder is known kept in order; append_repaired and log_dropped, its own two notices; a data value JSON cannot write kept as text
cryptobench/shared/log/stderr.py : the stderr handler: INFO and above, event records left out
cryptobench/shared/log/stdout.py : the labelled lines other programs read (results:, wrote:, identity:, took:, error:) one column wide; line(), say(), last()
cryptobench/shared/log/tests/ : pytest tests of the event log: append_line, attach, the sink, emit and step, warn
cryptobench/shared/log/warn.py : warn(): a `warning:` line, added to the run's problems when it keeps a list, and one log event with the line's code
cryptobench/shared/paths/__init__.py : one interface to every path the Python modules use: `from cryptobench.shared import paths`
cryptobench/shared/paths/device_dirs.py : DeviceDirs(sdk): folders on a device per API level, POSIX paths
cryptobench/shared/paths/host.py : the user's and host's locations: home, the user's global.yaml and devices.yaml, the Android SDK and its platform-tools, the per-phone lock under the user cache
cryptobench/shared/paths/imports.py : the apps' source folders on the import path, for the facade's process and its children; in shared/paths because tools/paths_check.py allows sys.path and PYTHONPATH edits nowhere else
cryptobench/shared/paths/names.py : the file and folder names of a results folder, litter (desktop files no listing of a run counts), and CONTRACT: those shared with Kotlin
cryptobench/shared/paths/packaged.py : packaged(package, name) through importlib and a named constant per data file a package ships
cryptobench/shared/paths/repo.py : Repo and repo(root): one checkout's named locations
cryptobench/shared/paths/results.py : Results(root): the finished device folders of a results root, a session's folder; finished, a manifest without partial:
cryptobench/shared/paths/roots.py : code_root (this checkout), benchmark_root (the checkout a run measures), each with its environment variable
cryptobench/shared/paths/run_tree.py : RunTree: every file of one results folder; its sections Configuration, Discovery, Preparation, Measurement, Analysis, Charts, CheckFolder, InteropFolder, Scoped, Logs, Review; AppTree, GroupingTree
cryptobench/shared/paths/settings.py : against(settings_file, value), the rule for a path a Python-read settings key names; beside, Kotlin Beside.authored for the authored test set; in_temp
cryptobench/shared/results/__init__.py : package of a run's results folder, importing no app
cryptobench/shared/results/identity.py : a measuring run's identity (effective run block, selection digest, timed and runner code digests, capture runtime with facts.yaml's build, order, suppressed errors) and the dotted fields two identities differ in
cryptobench/shared/results/layout.py : the --discovery modes; results/<device_id>/[<suite>/]: unit_folder, staging, publishing into the device folder after the earlier unit, but for the paths a resumed run keeps, moves to superseded/<stamp>/, the temporary-folder warning
cryptobench/shared/results/lock.py : DeviceLock: `<folder>/.lock`, or a phone's lock file by take_key, by fcntl.flock (POSIX), the holder's pid; another process is device_busy, the holding one takes it again; a results root or a phone (pipeline.py) or a device folder (perf-repair)
cryptobench/shared/results/manifest.py : results/<device_id>/manifest.yaml: MANIFEST_DOC and MODES, files, counts, runtime, providers, input digests, units, the harness operations, energy mark, problems, the partial mark of a stopped run; files added beside a finished run; write(), the one manifest writer
cryptobench/shared/results/publish_unit.py : publish_unit(): a verification stage's staged folder published beside a finished run (its configuration under the stage's folder) or as a new device folder, the results: line, the manifest, the superseded report; Route, a stage's folder name and manifest files
cryptobench/shared/results/partial.py : a run that stopped: the partial record (reason, case runs per process folder) its manifest is written with, a failed write one warning
cryptobench/shared/results/run_record.py : a measuring run's record: its identity, energyAcceptUnresponsive and the checkout's commit and clean, held by every block record and the manifest's run:; RUN_KEYS and FLAGS, the DATA / NOT_DATA table, and the refusal of an unresolved DATA value; changed without the checkout
cryptobench/shared/results/run_inputs.py : digests of a run's inputs, providers.bundled and global.yaml with its test set (analysis left out), for the manifest and --identify
cryptobench/shared/results/select.py : the device folder of a results root a reader names, or the only one there
cryptobench/shared/results/skipped.py : skip records of skipped.yaml (SKIPPED_DOC) and report.yaml (REPORT_DOC), version-checked: stage, provider, type, name, caseId, code, reason
cryptobench/shared/session/__init__.py : package of a session: session.yaml, its targets against the devices adb lists, order groups
cryptobench/shared/session/document.py : Session; session.yaml read and checked whole, paths resolved against its folder, discovery and probeStore checked as pipeline.py takes them; a file that cannot be read stops
cryptobench/shared/session/targets.py : TargetSpec, Resolved; resolve: each target found by key, alias or serial, its order, config, suites and the session's discovery mode checked, a coded skip per bad target, the host after the last phone group; groups; nothing_to_measure
cryptobench/shared/session/tests/ : pytest tests of session.yaml and target resolution, one per fallback row
cryptobench/shared/settings/__init__.py : package of the run's settings readers the stages share
cryptobench/shared/settings/authored.py : read, the one Python reader of the authored global.yaml: its document, providers.bundled, selection.knownVectors against it, selection.testSet beside it by paths.beside
cryptobench/shared/settings/bundled.py : providers.bundled of global.yaml: for authored.read the providers section checked (unknown_keys, wrong_type), then its entries by bundled_rule and for repeats in config's order, build property of the app or host CLI, DeviceProbe argument, effective record and check
cryptobench/shared/settings/bundled_rule.py : one providers.bundled entry checked as contract's BundledProvider.parse checks it: shape, then artifact, create and alias forms; the create and name forms perf-repair's bundled catalog reuses
cryptobench/shared/settings/defaults.py : defaults.yaml read through importlib.resources, by dotted path: the value :config writes for a key a config leaves out
cryptobench/shared/settings/defaults.yaml : package data written by :config DefaultsDocument (DefaultsFileTest pins it): run and analysis defaults, the energy capture and source a node without them gets
cryptobench/shared/settings/effective_view.py : the KEY table of effective.yaml (path, read rule, honoured on --bench); RunView, GateView, AnalysisView, EnergyView; the keys a host run ignores; effective.yaml with the warnings and skips of report.yaml
cryptobench/shared/settings/energy_capture.py : a node's energy capture and source against the default; a copy of the energy scripts' capture.py, kept equal by a test
cryptobench/shared/stats/__init__.py : package of the benchmark's calculations, with no I/O: descriptive statistics, the run count's equations, tests across processes, display units
cryptobench/shared/stats/descriptive.py : one definition of each per-case statistic: mean, sample SD, CoV, interpolated quantiles, IQR, QCD; which one leads
cryptobench/shared/stats/equations.py : every calculation the run count uses, and the median's binomial ranks; no I/O
cryptobench/shared/stats/inference.py : over one value per process or one process's samples: Shapiro-Wilk, QQ r and its seeded critical value, Mann-Whitney (exact or normal), Cliff's delta, bootstrap ratio of medians, drift between thirds; no I/O
cryptobench/shared/stats/units.py : DisplayUnits: nanoseconds per call in the chosen latency and throughput units; significant-figure numbers
cryptobench/shared/stop/__init__.py : package of the terminator: the code table and terminate(); how a child process is stopped
cryptobench/shared/stop/child.py : stop(process, grace, poll): SIGTERM to the child's group, up to grace seconds, SIGKILL to the group, wait (a Ctrl-C during the grace kills at once); PIPELINE_GRACE_SECONDS 120; stop_like_ctrl_c(): SIGTERM and SIGHUP raise KeyboardInterrupt
cryptobench/shared/stop/codes.py : the code table, loaded from the glossary: every stop, warn and skip code once with its default action, the actions stops.<code> may choose (none: fixed, and why), exit and next step
cryptobench/shared/stop/terminate.py : terminate(): the action resolved, one finding event with data.code, action and next (the code's, or next_step), then Halt, warn or skip; halt_of(): a fixed stop's Halt handed back
cryptobench/shared/stop/tests/ : pytest tests of the code table, halt_of and the child stop
cryptobench/shared/versions/__init__.py : package of dependency versions
cryptobench/shared/versions/order.py : a Gradle version: pinned or not; newest of several
cryptobench/stages/__init__.py : package of the run's stages, one package each, importing none of them
cryptobench/stages/analysis/__init__.py : package of the analysis stage
cryptobench/stages/analysis/not_measured.py : planned timed cases the final benchmark.json lacks: one not_measured line each, recorded in the manifest
cryptobench/stages/analysis/scripts.py : the analysis scripts over a measured benchmark.json, by path; the first that fails is one charts_failed warning
cryptobench/stages/analysis/tests/ : pytest tests of the analysis stage
cryptobench/stages/configuration/__init__.py : package of the configuration stage
cryptobench/stages/configuration/config_check.py : the parse-only check of a global.yaml and its test set before any build, through CheckConfigKt; providers.bundled from its output
cryptobench/stages/configuration/global_file.py : the global.yaml a run reads: --config, CRYPTOBENCH_CONFIG, the user's, the repository's
cryptobench/stages/configuration/guide.py : after effective.yaml: exactly its items picked from the implementation guide, written as guide.yaml beside it; one fallback line per provider
cryptobench/stages/configuration/tests/ : pytest tests of the configuration stage; test_recipe_trees.py writes and checks tests/contracts/catalogue/recipe-trees.yaml
cryptobench/stages/discovery/__init__.py : package of the discovery stage
cryptobench/stages/discovery/capture_files.py : the capture, trial and requirements a discovery wrote, by path and paired by stamp; never the newest in a kept folder; the reuse that probed again
cryptobench/stages/discovery/discover.py : discover and configure: probe or host discovery, ConfigureKt, effective.yaml summary; three end states: in place, staged (the caller publishes), published under the capture's device id
cryptobench/stages/discovery/build_versions.py : a device's security patch and Conscrypt and ART APEX versions, for facts.yaml's build section
cryptobench/stages/discovery/facts.py : device facts into discovery/facts.yaml
cryptobench/stages/discovery/probe.py : DeviceProbe on the device: the plan directory emptied, the probe run, its capture and trial pulled into discovery/
cryptobench/stages/discovery/probe_store.py : --discovery verify: the build key, the stored capture+trial it names reused unchanged, else the probe's stored; why each path
cryptobench/stages/discovery/tests/ : pytest tests of the discovery stage
cryptobench/stages/measurement/__init__.py : package of the measurement stage
cryptobench/stages/measurement/benchmark.py : the plain run's benchmark: device passes and sessions or host processes, warm-up, dry pass; whether it timed anything, for the analysis; the energy interpreter check passed in
cryptobench/stages/measurement/case_files.py : process-N/cases/<case>.json: the path of a case's pulled benchmarkData, the folder made per process, benchmarkData.json merged from the files; process-N/order.txt, the launch order
cryptobench/stages/measurement/energy/__init__.py : package of the energy steps of a --device run on the host
cryptobench/stages/measurement/energy/install.py : an energy source's packages installed on first use into a venv per source and requirements digest under the user cache
cryptobench/stages/measurement/energy/session.py : Perfetto sessions on the device: start, stop, pull
cryptobench/stages/measurement/energy/sources/ : one adapter per energy.source on the host; how the host runs apps/benchmark-runner/energy
cryptobench/stages/measurement/energy/steps.py : energy steps of a --device run: capture selection, the run's energy source
cryptobench/stages/measurement/measuring.py : what a run's device sessions share: the Measuring context, the thermal gate's start, the androidx arguments of a session and a pass, timed hooks, ConvertKt, per-process files and core pins; the energy pre-flight and the end idle reading with its reconversion
cryptobench/stages/measurement/resume.py : the run's record; at a measuring run's publish the RedoPlan: the blocks of a stopped run with the same identity that stay in place, verified and content-checked, and the kept runs' failing cases launched again; the resumed, redo, identity_changed and block_unverified lines; the manifest's resumed: note
cryptobench/stages/measurement/session/__init__.py : package of one device measuring session: processes, cases, passes, order, warm-up, hooks
cryptobench/stages/measurement/session/blocks.py : run.resumeBlockRuns: a pass's runs in blocks, a recorded block kept (its redo runs launched again and its record rewritten), any other measured then recorded; the block record (identity, runId, runs, boot id, problems, relaunched, findings, files); the digests of runs a host step rewrote refreshed
cryptobench/stages/measurement/session/case_isolation.py : one case's instrumentation process and its pull, the device's case listing
cryptobench/stages/measurement/session/clocks_hook.py : session hook: the clock state around every process and case into clocks.yaml
cryptobench/stages/measurement/session/cooldown_hook.py : session hook: run.caseCooldownSeconds of host sleep between measured cases, one line per pass
cryptobench/stages/measurement/session/dynamic_temperature.py : run.thermalGate facade: the startup decision, hold, verdict and start margin; the only caller of start_margin's functions
cryptobench/stages/measurement/session/energy_hook.py : session hook: the energy source's window around a process, traces pulled per case, dry pass, joules
cryptobench/stages/measurement/session/gate_history.py : what one temperature gate session did: per-case waits and discards for thermal.json, its per-pass line
cryptobench/stages/measurement/session/launch.py : the only place a timed run of a case starts: hold, launch, verdict, check_case, rejected/, retries, relaunched entries
cryptobench/stages/measurement/session/measure.py : one device measuring session of the benchmark: processes, a process per case, hooks, check_run at a process's end with its cases launched again; a process repetition's folder and line, a case's progress line
cryptobench/stages/measurement/session/passes.py : run.passes: PASS_ROWS (metrics, keeps capture, cleaned, owned key, sizing) and pass_views from RunView; one device session per metric group, its device arguments and conversion, the merge per metric; MergeRunsKt over process repetitions
cryptobench/stages/measurement/session/skips.py : a skipped.yaml record (caseId, code) whose code codes.yaml holds as an outcome or an error: a final skip, its case_skipped line
cryptobench/stages/measurement/session/thermal_hook.py : session hook: temperature around every process and case into thermal.json with the gate's history, its lines per pass
cryptobench/stages/measurement/session/variant_order.py : run.variants on a device: an item's fixed and notFixed cases adjacent, A/B then B/A over repetitions; run.orderSeed's per-process shuffle; the order's identity stanza
cryptobench/stages/measurement/session/window.py : run.passes.energy.minWindowSeconds: a case's window from its pulled file, one relaunch at 1.5 x the minimum, short_window, energy-samples.yaml
cryptobench/stages/measurement/session/warmup.py : run.warmup: a pre-flight run of a few planned cases before the first pass, final skips left out and chosen again, off at 0 iterations; its output never pulled
cryptobench/stages/measurement/start_margin.py : the temperature gate's start margin: hot, clean and ignored outcomes, the start limit and how the margin moves; no I/O
cryptobench/stages/measurement/tests/ : pytest tests of the measurement stage
cryptobench/stages/measurement/validation/__init__.py : package of result validation: the rules table, the expectation it reads, rejected attempts, validation.yaml, the audit
cryptobench/stages/measurement/validation/audit.py : pipeline.py --audit: every measured unit under a results root read only, per case runs, relaunches, rejected attempts, findings, outliers; audit.yaml
cryptobench/stages/measurement/validation/expectation.py : what a run of one pass promised, from the run record's run block: samples per case, minimum window
cryptobench/stages/measurement/validation/rejected.py : rejected/<UTC>/[<pass>/]process-<n>/<case>.json with why.yaml: an attempt that failed a rule
cryptobench/stages/measurement/validation/report.py : validation.yaml: per run the last check_run result; the block end's checker
cryptobench/stages/measurement/validation/rules.py : the one rules table (code, scope, severity, check), Finding, Result, RunFolder, check_case, check_run
cryptobench/stages/measurement/thermal.py : device temperatures from dumpsys thermalservice: sensors by HAL name, status, sentinels skipped, unavailable as a reason; the skin and CPU extremes a line prints
cryptobench/stages/verification/__init__.py : package of the verification stage
cryptobench/stages/verification/check.py : --check run: every planned case once through the real harness (host CheckKt, device EndToEndCheck under the dry run), check.yaml, its summary and failures, published beside a finished run or as a new device folder; discovery's steps passed in
cryptobench/stages/verification/harness.py : --harness run: scope generation, ScopedInterop on the device, interop verdicts into checked/; discovery and the entry point's error reporting passed in
cryptobench/stages/verification/interop.py : --interop run: the plan's pairs on the host or device, published beside a finished run or as a new device folder; discovery's steps passed in
cryptobench/stages/verification/interop_oracle.py : oracle steps of a --interop run: plan staging, host InteropKt, device InteropCheck, summary
cryptobench/stages/verification/known_answers.py : --check's known-answers.yaml: the guide's vectors filled per provider, global.yaml's selection.knownVectors
cryptobench/stages/verification/scope/__init__.py : package of the --harness run's sources: harness.yaml to compiled wrappers, interop plan, device verdicts; the harness code digest
cryptobench/stages/verification/scope/code_digest.py : the digest of the code from a harness.yaml to a checked harness; a pattern matching nothing is an error
cryptobench/stages/verification/scope/compile.py : compiles the android test sources with Gradle; the compiler's error lines
cryptobench/stages/verification/scope/dependencies.py : a scope's dependencies: imported, language-provided, stubbed, deferred or unsatisfied
cryptobench/stages/verification/scope/generate.py : harness.yaml to generated scope sources and scoped-plan.yaml; per-scope compile on failure
cryptobench/stages/verification/scope/harness.py : reads perf-repair's harness.yaml
cryptobench/stages/verification/scope/inputs.py : synthesisable parameter types and the value or ScopeInputs and ScopeKeys call that builds each
cryptobench/stages/verification/scope/interop.py : each scope's interop check: round trip with its partner by inverse link, output_changes for an upgrade, same output, or none
cryptobench/stages/verification/scope/languages.py : per-language row for scope sources: parser, suffix, statement end, provided names, tag stub, wrapper template
cryptobench/stages/verification/scope/results.py : device interop verdicts into scoped-plan.yaml
cryptobench/stages/verification/scope/signature.py : Java method and Kotlin function header parser; header as a public static member
cryptobench/stages/verification/scope/wrapper.py : renders the per-variant wrappers and the GeneratedScopes catalog
cryptobench/stages/verification/tests/ : pytest tests of the verification stage
pyproject.toml : the shared library's package metadata
```
