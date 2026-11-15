# lib/cryptobench

The implementation guide under `algorithms/` and the Python that reads it, shared by `apps/benchmark-runner` and `apps/perf-repair`. Data never lives here; readers never live in `algorithms/`.

```
../../algorithms/ : data: `<family>_catalogue.yaml` per family, one entry per id `<type>|<canonical>` (key, required, optional, conditions, lifecycle, operations, contract, sourcedOnly, providers, provenance); `common.yaml` sources, keyStrength maps, deterministicRelied; `recipes.yaml` how each parameter object a row names is made; `deviations.yaml` facts shared by a set of names and builds, stated once;
../../algorithms/algorithm-names.yaml : canonical name ← spellings per engine type; key-size suffixes; transformation modes, paddings, per-algorithm synonyms; key formats
../../algorithms/families.yaml : predefined families with fixed descriptions, the one copy
../../algorithms/glossary.yaml : data: one defined meaning per key and value of groups.yaml, the catalogues, recipes.yaml, deviations.yaml, provider-builds.yaml and algorithm-names.yaml, a tree with sections group, algorithm, recipe, plan, deviation, build and names
../../algorithms/groups.yaml : data: per family its exemplars and the listed algorithm ids, from whose catalogue contracts the contract rows come; a person adds ids from group-candidates.yaml
../../algorithms/interchange.yaml : data: per engine type the components that split a group, the rules that read them from a canonical name, what a missing key contract means, and which contract each component states
../../algorithms/provider-builds.yaml : data: every provider build the catalogues' measured facts ran on, keyed <name> @ <build>, with what each says of itself; a behaviour true of a provider and the ids it reaches
../../algorithms/vectors/ : known answers by family
cryptobench/__init__.py : package of the Python library the benchmark runner and perf-repair share
cryptobench/pipeline/__init__.py : package of the run's stage framework, importing no stage
cryptobench/pipeline/stage.py : StageContext (options, configuration, device, the parse-only check's answer, the run's problems list), what each stage reads; Stage, a stage's shape
cryptobench/pipeline/took.py : the took: line of a timed step
cryptobench/pipeline/warn.py : a stage's warning: line, added to the run's problems when it keeps a list
cryptobench/shared/__init__.py : package of the components the stages share, importing neither the pipeline nor a stage
cryptobench/shared/catalogue/__init__.py : package of the implementation guide's readers
cryptobench/shared/catalogue/algorithms.py : reader of the catalogues, checked whole: entry fields, sources, contracts, type facts, provider overrides; lookup by family and id
cryptobench/shared/catalogue/deviations.py : reads algorithms/deviations.yaml, every word a glossary term; what an entry's providers holds once provider behaviours and deviations apply
cryptobench/shared/catalogue/families.py : the family catalog and (engine type, key kind) → family
cryptobench/shared/catalogue/glossary.py : what_is: a term, a subtree or one value's meaning of glossary.yaml; term_problems: an entry's words checked against it
cryptobench/shared/catalogue/grouping.py : Family, Item (key: what a record names), Profile (isolated: a generator of unknown key contract); key contract values, labels and sources; items.json (schema 1) and profiles.json (schema 5) documents; provider_of, algorithm_of
cryptobench/shared/catalogue/groups.py : reader of groups.yaml, checked whole: one group per family by id, contract rows from each member's catalogue contract, a row at each key contract
cryptobench/shared/catalogue/guide_items.py : guide_items: what the guide says for one effective.yaml's items at this device's builds
cryptobench/shared/catalogue/interchange.py : reader of interchange.yaml: engines, rules by canonical name; a component outside its splits is refused
cryptobench/shared/catalogue/names.py : the names reader: Canonical (name, keySize, known), engine types (what detection scans), fold, same_engine, key formats, name_conflict, key_or_spelling (a conflict keys by its spelling)
cryptobench/shared/catalogue/overrides.py : a provider override's path in an entry, and one build's differences applied to a copy
cryptobench/shared/catalogue/provider_builds.py : reads provider-builds.yaml; a build key from what a probe records; a name resolves to one key or is provider_build_unknown
cryptobench/shared/catalogue/recipes.py : reads recipes.yaml, checked whole: one form per recipe, every word and each role's make and lives against the glossary, typed arguments, nested recipes present; the roles a recipe passes
cryptobench/shared/catalogue/reinit.py : whether init runs before every use of an operation, from one build's view of an entry
cryptobench/shared/catalogue/signature.py : Signature and its components, known, convention or unknown; decided, assumed, identity, differing
cryptobench/shared/catalogue/types.py : TypeRow: an algorithm's output kind, Properties, Strength, minSdk and their sources
cryptobench/shared/catalogue/vectors.py : known answers: read and checked whole, filled per provider for one run, --check's coverage lines
cryptobench/shared/catalogue/views.py : what an agent is shown: one entry with only its provider build's overrides (view_for), the groups' ids, descriptions and exemplars (list_groups), one group's members a page at a time (get_group)
cryptobench/shared/document/__init__.py : package of the YAML document reader and writer and the JSON document writer
cryptobench/shared/document/document.py : parse_yaml, a YAML text as its one shape (a mapping unless named) or invalid_yaml at its line and column; DocumentKind: a versioned document's accepted schemaVersion (one or several), its reader's refusal text and error type; check, the one schemaVersion check every reader calls
cryptobench/shared/document/dump.py : dump_yaml, a value as YAML text through one named profile (BLOCK, FLOW_LEAVES, WIDE, UNICODE, WIDE_UNICODE), each the option set its writers have always written
cryptobench/shared/document/json_dump.py : json_text, a document as JSON text (indent 1); write_json, that text through write_text
cryptobench/shared/document/write.py : write_text, a file replaced whole through a temporary of its writer's own (mode as a plain open gives, fsync and folder fsync when durable, exclusive refuses an existing file); Staging, the temporary's name, mode and fsync per writer (STAGED, MANIFEST); write_texts, several files staged then renamed in order
cryptobench/shared/device/__init__.py : package of the host's device steps, importing no app
cryptobench/shared/device/adb.py : adb steps of a --device run: identity by getprop, install, probe, push, AOT compile, instrument and its OK line, clear, pull, scope check
cryptobench/shared/device/capture.py : a capture's runtime block, its schema version checked; the guide's platform name for it
cryptobench/shared/device/clocks.py : per-core cpufreq over adb; clocks.yaml and cpuLocked
cryptobench/shared/device/gradle_runner.py : runs one command of apps/benchmark/cli by its main class; filters its failure to the tool's own lines
cryptobench/shared/device/identity.py : device id from a capture's runtime block
cryptobench/shared/device/push.py : a device run's plan push, the suppressErrors warning, then the energy settle's files
cryptobench/shared/device/timeouts.py : ceilings of the host's subprocess steps (adb, install, instrument, case, gradle, compile, energy, analysis); expiry is one coded error
cryptobench/shared/digest/__init__.py : package of the digests over bytes
cryptobench/shared/digest/tree.py : byte_digest, the sha256 of some bytes; file_digest, of a file's bytes, None when absent; tree_digest, one digest of files in a given order, each its path under a root and its byte digest
cryptobench/shared/errors/__init__.py : package of the coded errors, importing nothing from the repo
cryptobench/shared/errors/coded.py : CODE and code_in, the code word a failure message starts with; code_of, the code a failure carries as `.code`; Coded, the marker of a failure whose message is its coded line (adds no ValueError base)
cryptobench/shared/errors/failures.py : AgentFailed (a provider's one coded failure line), GateError (the app gate's coded reasons), BenchmarkRunError (a pipeline.py run that failed), each on its own base; EnergyError (an energy source failed); CommandError (the runner's library code ends the run, its entry point prints the line)
cryptobench/shared/errors/codes.yaml : the glossary: every code once with its kind, its default action where a reader resolves it, an alias setting's values, perf-repair's stops.<code> entry
cryptobench/shared/errors/glossary.py : codes.yaml read through importlib.resources; Code: one code's default action, the actions stops.<code> may choose (none: fixed, and why), exit and next step; the action stop
cryptobench/shared/errors/halt.py : Halt, the exception terminate raises after its event
cryptobench/shared/errors/input_error.py : InputError, the one coded error a refused input raises (`.code`, `.path`, `.detail`)
cryptobench/shared/errors/line.py : one_line, a failure as one line of at most limit characters (500 unless given)
cryptobench/shared/errors/policy.py : the stops reader the settings layer installs; a code's action, its default without one; resolve, an alias setting's value to its code's action
cryptobench/shared/errors/validation.py : ValidationFailed, code artifact_invalid, and require: the stage gate
cryptobench/shared/paths/__init__.py : one interface to every path the Python modules use: `from cryptobench.shared import paths`
cryptobench/shared/paths/device_dirs.py : DeviceDirs(sdk): folders on a device per API level, POSIX paths
cryptobench/shared/paths/host.py : the user's and host's locations: home, the user's global.yaml, the Android SDK and its platform-tools
cryptobench/shared/paths/imports.py : the apps' source folders on the import path, for this process and a child
cryptobench/shared/paths/names.py : the file and folder names of a results folder, and CONTRACT: those shared with Kotlin
cryptobench/shared/paths/packaged.py : packaged(package, name) through importlib and a named constant per data file a package ships
cryptobench/shared/paths/repo.py : Repo and repo(root): one checkout's named locations
cryptobench/shared/paths/results.py : Results(root): the device folders of a results root
cryptobench/shared/paths/roots.py : code_root (this checkout), benchmark_root (the checkout a run measures), each with its environment variable
cryptobench/shared/paths/run_tree.py : RunTree: every file of one results folder; its sections Configuration, Discovery, Preparation, Measurement, Analysis, Charts, CheckFolder, InteropFolder, Scoped, Logs, Review; AppTree, GroupingTree
cryptobench/shared/paths/settings.py : against(settings_file, value), the one rule for a path a settings file names; in_temp
cryptobench/shared/results/__init__.py : package of a run's results folder, importing no app
cryptobench/shared/results/layout.py : results/<device_id>/: staging, publishing into the device folder, the temporary-folder warning
cryptobench/shared/results/manifest.py : results/<device_id>/manifest.yaml: files, counts, runtime, providers, input digests, units, the harness operations, energy mark, problems; files added beside a finished run
cryptobench/shared/results/run_inputs.py : digests of a run's inputs, providers.bundled and global.yaml with its test set (analysis left out), for the manifest and --identify
cryptobench/shared/results/select.py : the device folder of a results root a reader names, or the only one there
cryptobench/shared/settings/__init__.py : package of the run's settings readers the stages share
cryptobench/shared/settings/bundled.py : providers.bundled of global.yaml: the digest's raw read, build property of the app or host CLI, DeviceProbe argument, effective record and check
cryptobench/shared/settings/effective_view.py : effective.yaml with the warnings and skips of report.yaml
cryptobench/shared/settings/energy_capture.py : a node's energy capture and source against the default; a copy of the energy scripts' capture.py, kept equal by a test
cryptobench/shared/stats/__init__.py : package of the benchmark's calculations, with no I/O: descriptive statistics, the gate's and run count's equations, display units
cryptobench/shared/stats/descriptive.py : one definition of each per-case statistic: mean, sample SD, CoV, interpolated quantiles, IQR, QCD; which one leads
cryptobench/shared/stats/equations.py : every calculation the temperature gate and the run count use; no I/O
cryptobench/shared/stats/units.py : DisplayUnits: nanoseconds per call in the chosen latency and throughput units; significant-figure numbers
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
cryptobench/stages/configuration/tests/ : pytest tests of the configuration stage
cryptobench/stages/discovery/__init__.py : package of the discovery stage
cryptobench/stages/discovery/capture_files.py : the capture, trial and requirements a discovery wrote, by path and paired by stamp; never the newest in a kept folder; the reuse that probed again
cryptobench/stages/discovery/discover.py : discover and configure: probe or host discovery, ConfigureKt, effective.yaml summary; three end states: in place, staged (the caller publishes), published under the capture's device id
cryptobench/stages/discovery/facts.py : device facts into discovery/facts.yaml
cryptobench/stages/discovery/tests/ : pytest tests of the discovery stage
cryptobench/stages/measurement/__init__.py : package of the measurement stage
cryptobench/stages/measurement/energy/__init__.py : package of the energy steps of a --device run on the host
cryptobench/stages/measurement/energy/session.py : Perfetto sessions on the device: start, stop, pull
cryptobench/stages/measurement/energy/sources/ : one adapter per energy.source on the host; how the host runs apps/benchmark-runner/energy
cryptobench/stages/measurement/energy/steps.py : energy steps of a --device run: capture selection, the run's energy source
cryptobench/stages/measurement/tests/ : pytest tests of the measurement stage
cryptobench/stages/verification/__init__.py : package of the verification stage
cryptobench/stages/verification/check.py : --check run: every planned case once through the real harness (host CheckKt, device EndToEndCheck under the dry run), check.yaml, its summary and failures
cryptobench/stages/verification/interop.py : --interop run: the plan's pairs on the host or device, published beside a finished run or as a new device folder; discovery's steps passed in
cryptobench/stages/verification/interop_oracle.py : oracle steps of a --interop run: plan staging, host InteropKt, device InteropCheck, summary
cryptobench/stages/verification/known_answers.py : --check's known-answers.yaml: the guide's vectors filled per provider, global.yaml's selection.knownVectors
cryptobench/stages/verification/tests/ : pytest tests of the verification stage
pyproject.toml : the shared library's package metadata
```
