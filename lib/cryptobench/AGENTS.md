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
cryptobench/pipeline/stage.py : StageContext (options, configuration, device, the run's problems list), what each stage reads; Stage, a stage's shape
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
cryptobench/shared/document/__init__.py : package of the YAML document reader and writer
cryptobench/shared/document/document.py : parse_yaml, a YAML text as its one shape (a mapping unless named) or invalid_yaml at its line and column; DocumentKind: a versioned document's accepted schemaVersion (one or several), its reader's refusal text and error type; check, the one schemaVersion check every reader calls
cryptobench/shared/document/dump.py : dump_yaml, a value as YAML text through one named profile (BLOCK, FLOW_LEAVES, WIDE, UNICODE, WIDE_UNICODE), each the option set its writers have always written
cryptobench/shared/document/write.py : write_text, a file replaced whole through a temporary of its writer's own (mode as a plain open gives, fsync and folder fsync when durable, exclusive refuses an existing file); Staging, the temporary's name, mode and fsync per writer (STAGED, MANIFEST); write_texts, several files staged then renamed in order
cryptobench/shared/digest/__init__.py : package of the digests over bytes
cryptobench/shared/digest/tree.py : byte_digest, the sha256 of some bytes; tree_digest, one digest of files in a given order, each its path under a root and its byte digest
cryptobench/shared/errors/__init__.py : package of the coded errors, importing nothing from the repo
cryptobench/shared/errors/coded.py : CODE and code_in, the code word a failure message starts with; code_of, the code a failure carries as `.code`; Coded, the marker of a failure whose message is its coded line (adds no ValueError base)
cryptobench/shared/errors/failures.py : AgentFailed (a provider's one coded failure line), GateError (the app gate's coded reasons), BenchmarkRunError (a pipeline.py run that failed), each on its own base; EnergyError (an energy source failed), one class whichever name energy/sources loads under; CommandError (the runner's library code ends the run, its entry point prints the line)
cryptobench/shared/errors/codes.yaml : the glossary: every code once with its kind, its default action where a reader resolves it, an alias setting's values, perf-repair's stops.<code> entry
cryptobench/shared/errors/glossary.py : codes.yaml read through importlib.resources; Code: one code's default action, the actions stops.<code> may choose (none: fixed, and why), exit and next step; the action stop
cryptobench/shared/errors/halt.py : Halt, the exception terminate raises after its event
cryptobench/shared/errors/input_error.py : InputError, the one coded error a refused input raises (`.code`, `.path`, `.detail`)
cryptobench/shared/errors/policy.py : the stops reader the settings layer installs; a code's action, its default without one; resolve, an alias setting's value to its code's action
cryptobench/shared/errors/validation.py : ValidationFailed, code artifact_invalid, and require: the stage gate
cryptobench/shared/paths/__init__.py : one interface to every path the Python modules use: `from cryptobench.shared import paths`
cryptobench/shared/paths/device_dirs.py : DeviceDirs(sdk): folders on a device per API level, POSIX paths
cryptobench/shared/paths/host.py : the user's and host's locations: home, the user's global.yaml, the Android SDK
cryptobench/shared/paths/imports.py : the apps' source folders on the import path, for this process and a child
cryptobench/shared/paths/names.py : the file and folder names of a results folder, and CONTRACT: those shared with Kotlin
cryptobench/shared/paths/packaged.py : packaged(package, name) through importlib and a named constant per data file a package ships
cryptobench/shared/paths/repo.py : Repo and repo(root): one checkout's named locations
cryptobench/shared/paths/results.py : Results(root): the device folders of a results root
cryptobench/shared/paths/roots.py : code_root (this checkout), benchmark_root (the checkout a run measures), each with its environment variable
cryptobench/shared/paths/run_tree.py : RunTree: every file of one results folder; its sections Configuration, Discovery, Preparation, Measurement, Analysis, Charts, CheckFolder, InteropFolder, Scoped, Logs, Review; AppTree, GroupingTree
cryptobench/shared/paths/settings.py : against(settings_file, value), the one rule for a path a settings file names; in_temp
cryptobench/shared/stats/__init__.py : package of how a benchmark session decides
cryptobench/shared/stats/equations.py : every calculation the temperature gate and the run count use; no I/O
cryptobench/shared/stats/stats.py : one definition of each per-case statistic: mean, sample SD, CoV, interpolated quantiles, IQR, QCD; which one leads
cryptobench/shared/stats/units.py : DisplayUnits: nanoseconds per call in the chosen latency and throughput units; significant-figure numbers
pyproject.toml : the shared library's package metadata
```
