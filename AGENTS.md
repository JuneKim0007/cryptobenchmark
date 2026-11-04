# cryptobenchmark

## Route
- Kotlin, Python and shell code, module dependencies, comments → `agents/code.md`
- Gradle tests, module isolation, Android API check, Python tests, perf-repair check → `agents/testing.md`
- reviews and refactors: complexity, dead code, duplication, coverage, dependency commands → `agents/review.md`
- device runs: prerequisites, adb, `--suppress-errors`, core pinning, energy on a device → `agents/device.md`
- docs, guides, file maps, READMEs, any `.md` change → `agents/docs/writing.md`
- cross-module facts: architecture, run, results, energy, tools, cryptography catalogue → `docs/index.md`
- discovery: probe, trial, capture fields → `apps/benchmark/modules/environment/discovery/docs/index.md`
- config: authored files, inventory, effective, precedence → `apps/benchmark/modules/config/docs/index.md`
- settings: harness key table, device support → `apps/benchmark/modules/settings/docs/index.md`
- preparation: cases, keys, inputs, parameters → `apps/benchmark/modules/preparation/docs/index.md`
- benchmark: plan check, measurement, `benchmark.json` → `apps/benchmark/modules/benchmark/docs/index.md`
- android: instrumentation harness, device plan, core pinning → `apps/benchmark/modules/android/docs/index.md`
- perf-repair work → `apps/perf-repair/AGENTS.md`

## Rules
- layout: directives live in `AGENTS.md` and `agents/`; facts live in `docs/` and `apps/benchmark/modules/<m>/docs/`; `apps/perf-repair/` keeps its own router, guides and docs.
- change: one file, one responsibility.
- map: adding, moving or deleting a file updates its owning map in the same change.
- delete/rename: grep the symbol or path and remove its references first.
- delete/rename: re-grep and confirm zero hits.
- conflict: code wins; a guide or doc that disagrees with the code is corrected, never followed.
- check: after a code change, pass the commands in `agents/testing.md` for the touched area.
- check: after a docs or guide change, pass `python3 tools/docs_lint.py`.
- commit: never commit `results/`, `build/` or signing keys (`*.jks`).
- commit: no AI or tool attribution and no `Co-Authored-By` line in commit messages or PR bodies.

## Workflow
- module schema change: code → `-Dexamples.update=true` run → module doc
- harness setting: `Key` in `apps/benchmark/modules/settings/src/main/kotlin/Harness.kt` (`energy.*` in `EnergySettings.kt`, `cpu.*` in `CpuSettings.kt`) → field on the typed class → `apps/benchmark/modules/settings/docs/settings.md`
- module file added: its line in `apps/benchmark/modules/<m>/docs/index.md`
- guide change: `python3 tools/docs_lint.py`

## File structure

```
.github/workflows/docs.yml : CI docs lint
.github/workflows/jca-contract.yml : CI JCA contract tests on Java 17, 21, 25 and the Android API compile check
.github/workflows/modules.yml : CI isolated build and test per module
.github/workflows/tests.yml : CI Python suites and the root Gradle build: settings tests, androidTest compile
AGENTS.md : agent router
README.md : project entry page
agents/ : directive guides
apps/benchmark-runner/analysis/ : analysis of a benchmark.json: summary, charts, statistics
apps/benchmark-runner/bundled.py : providers.bundled of global.yaml: the digest's raw read, build property, DeviceProbe argument, effective check
apps/benchmark-runner/demo.sh : one-command host demo run into results/demo/<device_id>
apps/benchmark-runner/dependencies.py : the host modules a run needs, checked at its start; a missing one is one coded line and exit 1
apps/benchmark-runner/device/__init__.py : package of the attached device's reads: adb, id, clocks, temperatures, facts
apps/benchmark-runner/device/adb.py : adb steps of a --device run: identity by getprop, install, probe, push, AOT compile, instrument and its OK line, clear, pull, scope check
apps/benchmark-runner/device/clocks.py : per-core cpufreq over adb; clocks.yaml and cpuLocked
apps/benchmark-runner/device/facts.py : device facts into discovery/facts.yaml
apps/benchmark-runner/device/identity.py : device id from a capture's runtime block
apps/benchmark-runner/device/thermal.py : device temperatures from dumpsys thermalservice: sensors by HAL name, status, sentinels skipped, unavailable as a reason
apps/benchmark-runner/effective_view.py : effective.yaml with the warnings and skips of report.yaml
apps/benchmark-runner/energy/ : energy sources behind one seam (rails, manafa), pre-flight, joules per case, capture resolution
apps/benchmark-runner/energy_session.py : Perfetto sessions on the device: start, stop, pull
apps/benchmark-runner/energy_stage.py : energy steps of a --device run: capture selection, the run's energy source
apps/benchmark-runner/explain.py : each resolved setting of a run and the file it came from
apps/benchmark-runner/failure.py : one error line and exit; an error as one line of at most 500 characters
apps/benchmark-runner/global_file.py : the global.yaml a run reads: --config, CRYPTOBENCH_CONFIG, the user's, the repository's
apps/benchmark-runner/gradle_runner.py : runs one command of apps/benchmark/cli by its main class; filters its failure to the tool's own lines
apps/benchmark-runner/pipeline.py : run driver: options and refusals, stage order, one coded failure line; --probe (discover and configure only), --identify (device id, input and harness code digests, nothing written)
apps/benchmark-runner/repo.py : the repository root, the benchmark's Gradle root and the runner's folder every runner module resolves paths against
apps/benchmark-runner/results/__init__.py : package of a run's results folder: layout, manifest, input digests, device selection, per-case files
apps/benchmark-runner/results/case_files.py : process-N/cases/<case>.json: the path of a case's pulled benchmarkData, the folder emptied per process, benchmarkData.json merged from the files
apps/benchmark-runner/results/layout.py : results/<device_id>/: staging, publishing into the device folder, the atomic manifest write, the temporary-folder warning
apps/benchmark-runner/results/manifest.py : results/<device_id>/manifest.yaml: files, counts, runtime, providers, input digests, units, the harness operations, energy mark, problems; files added beside a finished run
apps/benchmark-runner/results/run_inputs.py : digests of a run's inputs, providers.bundled and global.yaml with its test set (analysis left out), for the manifest and --identify
apps/benchmark-runner/results/select.py : the device folder of a results root a reader names, or the only one there
apps/benchmark-runner/scope/__init__.py : package of the scoped run's sources: harness.yaml to compiled wrappers, interop plan, device verdicts
apps/benchmark-runner/scope/call_site.py : each swap's call site alone: the current and option item at the scope's sizes, operation and variant; one effective per selection and callsite.yaml for the device
apps/benchmark-runner/scope/code_digest.py : the digest of the code from a harness.yaml to a measured harness; a pattern matching nothing is an error
apps/benchmark-runner/scope/compile.py : compiles the android test sources with Gradle; the compiler's error lines
apps/benchmark-runner/scope/dependencies.py : a scope's dependencies: imported, language-provided, stubbed, deferred or unsatisfied
apps/benchmark-runner/scope/generate.py : harness.yaml to generated scope sources and scoped-plan.yaml; per-scope compile on failure
apps/benchmark-runner/scope/harness.py : reads perf-repair's harness.yaml
apps/benchmark-runner/scope/inputs.py : synthesisable parameter types and the value or ScopeInputs and ScopeKeys call that builds each
apps/benchmark-runner/scope/interop.py : each scope's interop check: round trip with its partner by inverse link, same output, or none
apps/benchmark-runner/scope/languages.py : per-language row for scope sources: parser, suffix, statement end, provided names, tag stub, wrapper template
apps/benchmark-runner/scope/results.py : device interop and call-site verdicts into scoped-plan.yaml; measured scopes and prepared call sites as prepared.yaml
apps/benchmark-runner/scope/signature.py : Java method and Kotlin function header parser; header as a public static member
apps/benchmark-runner/scope/wrapper.py : renders the per-variant wrappers and the GeneratedScopes catalog
apps/benchmark-runner/scope_generate.py : generate and compile a harness's scopes alone, sources left in place
apps/benchmark-runner/session/__init__.py : package of one device measuring session: processes, cases, passes, order, warm-up, hooks
apps/benchmark-runner/session/case_isolation.py : run.isolation case: one case's instrumentation process and its pull, the device's case listing
apps/benchmark-runner/session/clocks_hook.py : session hook: the clock state around every process and case into clocks.yaml
apps/benchmark-runner/session/cooldown_hook.py : session hook: run.caseCooldownSeconds of host sleep between measured cases, one line per pass
apps/benchmark-runner/session/energy_hook.py : session hook: the energy source's window around a process, traces pulled per case, dry pass, joules
apps/benchmark-runner/session/measure.py : one device measuring session for the benchmark and the before/after run: processes, a process per case or one for all, hooks; a process repetition's folder and line, a case's progress line
apps/benchmark-runner/session/passes.py : run.passes: one device session per metric group, its device arguments and conversion, the merge per metric; MergeRunsKt over process repetitions
apps/benchmark-runner/session/thermal_gate.py : run.thermalGate session hook: the idle baseline once before the warm-up, then a wait before each case process while the device is hotter, one line per pass
apps/benchmark-runner/session/thermal_hook.py : session hook: temperature around every process and case into thermal.json, one line per pass
apps/benchmark-runner/session/variant_order.py : run.variants on a device: an item's fixed and notFixed cases adjacent, A/B then B/A over repetitions
apps/benchmark-runner/session/warmup.py : run.warmup: a pre-flight run of a few planned cases once per device session, off at 0 iterations; its output never pulled
apps/benchmark-runner/stages/__init__.py : package of the run driver's stages: discover, benchmark, harness, interop, and their steps
apps/benchmark-runner/stages/benchmark.py : the plain run's benchmark: device passes and sessions or host processes, warm-up, dry pass, not_measured, analysis
apps/benchmark-runner/stages/capture_files.py : the capture and trial a discovery wrote, by path and paired by stamp; never the newest by a device-clock stamp; the reuse that probed again
apps/benchmark-runner/stages/config_check.py : the parse-only check of a global.yaml and its test set before any build, through CheckConfigKt; providers.bundled from its output
apps/benchmark-runner/stages/discover.py : discover and configure: probe or host discovery, ConfigureKt, effective.yaml summary, staged then published under the capture's device id
apps/benchmark-runner/stages/harness.py : --harness run: scope generation, the harness's device check, interop verdicts, scoped passes into measured/
apps/benchmark-runner/stages/interop.py : --interop run: the plan's pairs on the host or device, published beside a finished run or as a new device folder
apps/benchmark-runner/stages/interop_oracle.py : oracle steps of a --interop run: plan staging, host InteropKt, device InteropCheck, summary
apps/benchmark-runner/stages/measuring.py : what a run's device sessions share: the Measuring context, the thermal gate's start, session and pass arguments, timed hooks, plan push, ConvertKt, per-process files
apps/benchmark-runner/stages/not_measured.py : planned timed cases the final benchmark.json lacks: one not_measured line each, recorded in the manifest
apps/benchmark-runner/stages/took.py : the took: line of a timed step
apps/benchmark-runner/tests/ : pytest and standalone tests for apps/benchmark-runner/
apps/benchmark-runner/timeouts.py : ceilings of the host's subprocess steps (adb, install, instrument, case, gradle, compile, energy, analysis); expiry is one coded error
apps/benchmark/build.gradle : root buildscript: Android Gradle plugin and Kotlin plugin versions
apps/benchmark/cli/ : the host commands: probe, configure, parse-only check, bench, convert, merges, interop; JCA contract tests, examples
apps/benchmark/gradle.properties : Gradle daemon JVM args and AndroidX flags
apps/benchmark/gradlew : the one Gradle wrapper, for the benchmark's root build, its CLI build and every tools/ build
apps/benchmark/modules/android/ : instrumentation app: Jetpack harness, device plan, native core affinity
apps/benchmark/modules/benchmark/ : plan check and measurement of prepared cases; benchmark.json
apps/benchmark/modules/config/ : capture and trial to inventory.yaml; inventory and config/ to effective.yaml
apps/benchmark/modules/environment/discovery/ : provider and service probe, default-run trial, capture and trial YAML
apps/benchmark/modules/preparation/ : effective.yaml to prepared cases, each called once; prepared.yaml, skipped.yaml
apps/benchmark/modules/settings/ : harness key table shared by config, preparation and benchmark
apps/benchmark/settings.gradle : Gradle projects and their directories under apps/benchmark/modules/
apps/cli/facade.py : one command for benchmark then guided repair from one settings index; --check
apps/cli/facade/__init__.py : package of the facade: index, tree check, phases; the repository root; the runner and perfrepair on the path
apps/cli/facade/check.py : every path exists, each file through its real parser, each key where it belongs, the direction rule, the catalogs
apps/cli/facade/index.py : the root settings file: paths and what spans a run; any key it does not know is an error
apps/cli/facade/phases.py : the crypto and guided phases as guide children with every path named; one coded line each
apps/cli/facade/tree.py : the resolved tree: nodes, direction rule, printed lines, the document a run record keeps
apps/cli/tests/ : pytest for the facade
apps/perf-repair/ : cryptobenchmark results to crypto replacements worth testing in an app
config/ : authored run configuration: global settings and test sets
docs/ : cross-module fact docs
requirements.txt : every host Python dependency
settings.example.yaml : template for `settings.yaml`, the facade's root index
tools/android-api-check/ : compiles discovery, settings, preparation, benchmark against android.jar without the JDK
tools/docs_lint.py : docs and guide graph check: maps, coverage, index.md, edges, reachability, size, banned text
tools/lint/__init__.py : package of the docs lint's model of the repo
tools/lint/markdown.py : a guide's or doc's sections, fenced blocks, map lines and path tokens
tools/lint/paths.py : routers, guides, docs and graphed files by path
tools/lint/tree.py : the files git lists, their folders and markdown, and each named path resolved against them
tools/module-isolation/ : per-module isolated compile and test
tools/screening_list.py : writes apps/perf-repair/docs/screening-list.md from the screening catalog
tools/shared_functions.py : writes docs/shared-functions.md and apps/perf-repair/docs/shared-functions.md from the import graph
tools/tests/ : pytest for the repo dev tools
```
