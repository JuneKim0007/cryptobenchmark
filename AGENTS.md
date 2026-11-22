# cryptobenchmark

## Route
- Kotlin, Python and shell code, module dependencies, comments → `docs/contributing/code.md`
- Gradle tests, module isolation, Android API check, Python tests, perf-repair check → `docs/contributing/testing.md`
- reviews and refactors: complexity, dead code, duplication, coverage, dependency commands → `docs/contributing/review.md`
- device runs: prerequisites, adb, `--suppress-errors`, core pinning, energy on a device → `docs/contributing/device.md`
- docs, guides, file maps, READMEs, any `.md` change → `docs/contributing/writing.md`
- cross-module facts: architecture, run, results, energy, tools, cryptography catalogue → `docs/index.md`
- contract: capture, trial and requirements models and their YAML schemas → `apps/benchmark/modules/environment/contract/docs/index.md`
- discovery: probe, trial, capture fields → `apps/benchmark/modules/environment/discovery/docs/index.md`
- config: authored files, inventory, effective, precedence → `apps/benchmark/modules/config/docs/index.md`
- settings: harness key table, device support → `apps/benchmark/modules/settings/docs/index.md`
- records: `Skip`, `StoppedOnFailureException` → `apps/benchmark/modules/records/docs/index.md`
- catalogue: `EngineRows`, setup-catalog.yaml's rows → `apps/benchmark/modules/catalogue/docs/index.md`
- files: every Kotlin file and folder name, stamps, beside-a-file rules → `apps/benchmark/modules/files/docs/index.md`
- jca: the catch rule, provider error text → `apps/benchmark/modules/jca/docs/index.md`
- document: the YAML codec and its profiles, typed field reads → `apps/benchmark/modules/document/docs/index.md`
- preparation: cases, keys, inputs, parameters → `apps/benchmark/modules/preparation/docs/index.md`
- benchmark: plan check, measurement, `benchmark.json` → `apps/benchmark/modules/benchmark/docs/index.md`
- android: instrumentation harness, device plan, core pinning → `apps/benchmark/modules/android/docs/index.md`
- perf-repair work → `apps/perf-repair/AGENTS.md`

## Rules
- layout: directives live in `AGENTS.md` and `docs/contributing/`; facts live in the rest of `docs/` and `apps/benchmark/modules/<m>/docs/`; `apps/perf-repair/` keeps its own router, guides and docs.
- change: one file, one responsibility.
- map: adding, moving or deleting a file updates its owning map in the same change.
- delete/rename: grep the symbol or path and remove its references first; re-grep and confirm zero hits.
- conflict: code wins; a guide or doc that disagrees with the code is corrected, never followed.
- check: after a code change, pass the commands in `docs/contributing/testing.md` for the touched area.
- check: after a docs or guide change, pass `python3 tools/docs_lint.py`.
- commit: never commit `results/`, `build/` or signing keys (`*.jks`).
- commit: no AI or tool attribution and no `Co-Authored-By` line in commit messages or PR bodies.

## Workflow
- module schema change: code → `-Dexamples.update=true` run → module doc
- harness setting: `Key` in `apps/benchmark/modules/settings/src/main/kotlin/Harness.kt` (`energy.*` in `EnergySettings.kt`, `cpu.*` in `CpuSettings.kt`) → field on the typed class → `apps/benchmark/modules/settings/docs/settings.md`
- module file added: its line in `apps/benchmark/modules/<m>/docs/index.md`

## File structure

```
.github/workflows/docs.yml : CI docs lint and the shared-functions drift check
.github/workflows/jca-contract.yml : CI JCA contract tests on Java 17, 21, 25 and the Android API compile check
.github/workflows/modules.yml : CI isolated build and test per module
.github/workflows/tests.yml : CI Python suites and the root Gradle build: settings tests, androidTest compile
AGENTS.md : agent router
README.md : project entry page
algorithms/ : the implementation guide: one catalogue per family, recipes, deviations, names, builds; map in lib/cryptobench/AGENTS.md
apps/benchmark-runner/analysis/ : analysis of a benchmark.json, run by path: summary, charts, statistics
apps/benchmark-runner/dependencies.py : the host modules a run needs, checked at its start, cryptobench from this checkout; a missing one is one coded line and exit 1
apps/benchmark-runner/energy/ : the energy scripts --energy-python runs: rails and manafa readings, pre-flight, joules per case, the capture rule
apps/benchmark-runner/explain.py : tool, not a pipeline step: each resolved setting of a run and the file it came from
apps/benchmark-runner/failure.py : one error line and exit; reported(), a CommandError as that line, around an entry point's main and passed into harness_run
apps/benchmark-runner/pipeline.py : run driver: stop signals as Ctrl-C, options and refusals, ROUTES (the first set option's stage runs on one StageContext, the plain run last; the routes compose the stages; a route that holds the device locks the phone by serial), one coded failure line; --probe (discover and configure only), --identify (device id, input and harness code digests, nothing written), --devices (adb's transports classified, before any config), --check-session (a session's plan, nothing run), --audit (a campaign's results read, audit.yaml written, before any config), --session (a session's targets as workers), --per-suite
apps/benchmark-runner/tests/ : pytest tests for apps/benchmark-runner/
apps/benchmark/build.gradle : root buildscript: Android Gradle plugin and Kotlin plugin versions
apps/benchmark/cli/ : the host commands: probe, configure, parse-only check, bench, end-to-end check and its diff, convert, merges, interop; JCA contract tests
apps/benchmark/gradle.properties : Gradle daemon JVM args and AndroidX flags
apps/benchmark/gradle/ : shared by the root, cli and tools/ builds: guide-resources.gradle puts the guide's names file on the classpath, libs.versions.toml holds the one SnakeYAML version, the wrapper
apps/benchmark/gradlew : the one Gradle wrapper, for the benchmark's root build, its CLI build and every tools/ build
apps/benchmark/modules/android/ : instrumentation app: Jetpack harness, device plan, native core affinity
apps/benchmark/modules/benchmark/ : plan check and measurement of prepared cases; benchmark.json
apps/benchmark/modules/catalogue/ : EngineRows, the one reading of setup-catalog.yaml's per-type rows config and preparation share
apps/benchmark/modules/config/ : capture and trial to inventory.yaml; inventory and config/ to effective.yaml
apps/benchmark/modules/document/ : the one YAML codec, a SnakeYAML setup per profile, and DocumentFields; shared by discovery, config, preparation and benchmark
apps/benchmark/modules/environment/contract/ : the discovery handoff documents: capture, trial and requirements models and YAML schemas, no JCA
apps/benchmark/modules/environment/discovery/ : provider and service probe, default-run and requirement trials, capture, trial and requirements YAML writers
apps/benchmark/modules/files/ : every Kotlin file and folder name, stamps and beside-a-file rules; python's CONTRACT agrees
apps/benchmark/modules/jca/ : the one catch rule and the provider-message scrubber every module that calls a provider shares
apps/benchmark/modules/preparation/ : effective.yaml to prepared cases, each called once; prepared.yaml, skipped.yaml
apps/benchmark/modules/records/ : Skip and StoppedOnFailureException, the records of left-out work config, preparation and benchmark share
apps/benchmark/modules/settings/ : harness key table shared by config, preparation and benchmark
apps/benchmark/settings.gradle : Gradle projects and their directories under apps/benchmark/modules/
apps/cli/facade.py : one command for benchmark then guided repair from one settings index; SIGTERM as Ctrl-C; --check
apps/cli/facade/__init__.py : package of the facade: index, tree check, phases; the repository root; the runner and perfrepair on the path
apps/cli/facade/check.py : every path exists, each file through its real parser, each key where it belongs, the direction rule, the catalogs
apps/cli/facade/index.py : the root settings file: paths and what spans a run; any key it does not know is an error
apps/cli/facade/phases.py : the crypto and guided phases as guide children with every path named, each in its own session and stopped with its grace when the facade is interrupted; one coded line each
apps/cli/facade/tree.py : the resolved tree: nodes, direction rule, printed lines, the document a run record keeps
apps/cli/tests/ : pytest for the facade
apps/perf-repair/ : cryptobenchmark results to crypto replacements applied per call site, compiled and interop-checked on a phone
config/ : every user-edited file by its reader: benchmark/ (global.yaml, testsets/), facade/ (the settings index template), perf-repair/ (perfrepair, targets and .env templates); README.md maps them with the files outside it and each lookup order
docs/ : cross-module fact docs
docs/contributing/ : directive guides
lib/cryptobench/ : the Python library the runner and perf-repair share: shared components, the stage framework, the run's stages; map in its AGENTS.md
pytest.ini : the Python apps' source folders, and the test folders other tests import, on the test path for pytest from the repository root
requirements.txt : every host Python dependency
tests/contracts/ : fixtures both languages' tests read: documents/, the .json value each must read a module example (config global and effective, preparation guide) to, and the facts and known-answers Python writes with theirs, beside-authored.json the test-set path cases (Kotlin the exact path text, Python the same location); yaml-codec/, scalar and string cases and a duplicate-key file; runner/thermal.json as the runner writes it; catalogue/key-types.yaml, an entry's key.type per provider both languages read; catalogue/recipe-trees.yaml, every recipe row's tree or refusal at each build, Python writing it (UPDATE_GOLDEN=1) and Kotlin's Recipes reading it
tools/android-api-check/ : compiles jca, document, contract, discovery, settings, records, catalogue, preparation, benchmark against android.jar without the JDK
tools/dead-code-allow.txt : vulture findings the dead-code check keeps, each with its reason
tools/dead_code.py : dead-code check: vulture minus the allowlist; local only, fails without vulture
tools/docs_lint.py : docs and guide graph check: maps, coverage, index.md, edges, reachability, size, banned text, names code must hold
tools/lint/__init__.py : package of the docs lint's model of the repo
tools/lint/claims.py : what a doc names that code must hold: source paths, perfrepair.yaml keys, stop codes, snake_case and dotted names
tools/lint/external-names.txt : names a doc may use that no tracked code holds, each with its reason
tools/lint/markdown.py : a guide's or doc's sections, fenced blocks, map lines and path tokens
tools/lint/paths.py : routers, guides, docs and graphed files by path
tools/lint/tree.py : the files git lists, their folders and markdown, and each named path resolved against them
tools/module-isolation/ : per-module isolated compile and test
tools/paths-frozen.txt : what tools/paths_check.py still finds, each with its reason; only shrinks
tools/paths_check.py : path rules outside lib/cryptobench/cryptobench/shared/paths/ and the linkage of every data file to a production reader; frozen list only shrinks
tools/screening_list.py : writes apps/perf-repair/docs/screening-list.md from the screening catalog
tools/shared_functions.py : writes docs/shared-functions.md and apps/perf-repair/docs/shared-functions.md from the import graph; --check fails on drift
tools/tests/ : pytest for the repo tools and repo-wide checks: lib layering, the runner holding only entry points, the error-code glossary both ways, the lib wheel's data
```
