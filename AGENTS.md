# cryptobenchmark

## Route
- Kotlin, Python and shell code, module dependencies, comments → `agents/code.md`
- Gradle tests, module isolation, Android API check, Python tests, perf-repair check → `agents/testing.md`
- device runs: prerequisites, adb, `--suppress-errors`, core pinning, energy on a device → `agents/device.md`
- docs, guides, file maps, READMEs, any `.md` change → `agents/docs/writing.md`
- cross-module facts: architecture, run, results, energy, tools, cryptography catalogue → `docs/index.md`
- discovery: probe, trial, capture fields → `modules/environment/discovery/docs/index.md`
- config: authored files, inventory, effective, precedence → `modules/config/docs/index.md`
- settings: harness key table, device support → `modules/settings/docs/index.md`
- preparation: cases, keys, inputs, parameters → `modules/preparation/docs/index.md`
- benchmark: plan check, measurement, `benchmark.json` → `modules/benchmark/docs/index.md`
- android: instrumentation harness, device plan, core pinning → `modules/android/docs/index.md`
- perf-repair work → `perf-repair/AGENTS.md`

## Rules
- layout: directives live in `AGENTS.md` and `agents/`; facts live in `docs/` and `modules/<m>/docs/`; `perf-repair/` keeps its own router, guides and docs.
- change: one file, one responsibility.
- map: adding, moving or deleting a file updates its owning map in the same change.
- delete/rename: grep the symbol or path and remove its references first.
- delete/rename: re-grep and confirm zero hits.
- conflict: code wins; a guide or doc that disagrees with the code is corrected, never followed.
- check: after a code change, pass the commands in `agents/testing.md` for the touched area.
- check: after a docs or guide change, pass `python3 scripts/docs_lint.py`.
- commit: never commit `results/`, `build/` or signing keys (`*.jks`).
- commit: no AI or tool attribution and no `Co-Authored-By` line in commit messages or PR bodies.

## Workflow
- module schema change: code → `-Dexamples.update=true` run → module doc
- harness setting: `Key` in `modules/settings/src/main/kotlin/Harness.kt` → field on the typed class → `modules/settings/docs/settings.md`
- module file added: its line in `modules/<m>/docs/index.md`
- guide change: `python3 scripts/docs_lint.py`

## File structure

```
.github/workflows/docs.yml : CI docs lint
.github/workflows/jca-contract.yml : CI JCA contract tests on Java 17, 21, 25 and the Android API compile check
.github/workflows/modules.yml : CI isolated build and test per module
AGENTS.md : agent router
README.md : project entry page
agents/ : directive guides
build.gradle : root buildscript: Android Gradle plugin and Kotlin plugin versions
config/ : authored run configuration: global settings and test sets
docs/ : cross-module fact docs
gradle.properties : Gradle daemon JVM args and AndroidX flags
modules/android/ : instrumentation app: Jetpack harness, device plan, native core affinity
modules/benchmark/ : plan check and measurement of prepared cases; benchmark.json
modules/config/ : capture and trial to inventory.yaml; inventory and config/ to effective.yaml
modules/environment/discovery/ : provider and service probe, default-run trial, capture and trial YAML
modules/preparation/ : effective.yaml to prepared cases, each called once; prepared.yaml, skipped.yaml
modules/settings/ : harness key table shared by config, preparation and benchmark
perf-repair/ : cryptobenchmark results to crypto replacements worth testing in an app
scripts/bundled.py : providers.bundled of global.yaml: build property, DeviceProbe argument, effective check
scripts/clocks.py : per-core cpufreq over adb; clocks.yaml and cpuLocked
scripts/demo.sh : one-command host demo run into results/demo
scripts/device.py : adb steps of a --device run: install, probe, push, AOT compile, measure, pull
scripts/device_args.py : instrumentation launch arguments for the plan's metrics (CPU events)
scripts/docs_lint.py : docs and guide graph check: maps, coverage, index.md, edges, reachability, size, banned text
scripts/effective_view.py : effective.yaml with the warnings and skips of report.yaml
scripts/energy_session.py : Perfetto sessions on the device: start, stop, pull
scripts/energy_stage.py : energy steps of a --device run: capture selection, pre-flight, tools/energy calls
scripts/explain.py : each resolved setting of a run and the file it came from
scripts/facts.py : device facts into discovery/facts.yaml
scripts/failure.py : one error line and exit
scripts/gradle_runner.py : runs a tools/ Gradle build; filters its failure to the tool's own lines
scripts/pipeline.py : run driver: stages in order, results/manifest.yaml
scripts/requirements.txt : host Python dependencies
scripts/tests/ : pytest and standalone tests for scripts/
settings.gradle : Gradle projects and their directories under modules/
tools/android-api-check/ : compiles discovery, settings, preparation, benchmark against android.jar without the JDK
tools/energy/ : rail pre-flight, joules per case, capture resolution
tools/jca-contract/ : host probe and configure commands, JCA contract tests, examples, shared tools Gradle wrapper
tools/module-isolation/ : per-module isolated compile and test
tools/quick-bench/ : host prepare and measure, Jetpack result conversion, run merge, analysis
```
