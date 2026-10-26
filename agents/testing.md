# Testing

## Calls
- `docs/architecture.md` : isolation build: which sources each module compiles with
- `docs/tools.md` : tools/ builds, commands and outputs

## Rules
- isolation: a change to discovery, config, preparation or benchmark passes `tools/jca-contract/gradlew -p tools/module-isolation :<m>:test` for each touched module (`discovery`, `config`, `preparation`, `benchmark`).
- isolation: a module that needs another module's classes outside the table in `docs/architecture.md` fails here; fix the dependency, never the isolation build.
- contract: a change to discovery, settings or config passes `tools/jca-contract/gradlew -p tools/jca-contract test`.
- android api: a change to discovery, settings, preparation or benchmark passes `tools/jca-contract/gradlew -p tools/android-api-check compileKotlin`; pass `-PandroidJar=<android.jar>` when `$ANDROID_HOME/platforms/android-36/android.jar` is absent.
- settings: a change to `:settings` passes `./gradlew :settings:test` from the repo root.
- examples: regenerate committed `example/` files only after a schema change: `tools/jca-contract/gradlew -p tools/module-isolation test -Dexamples.update=true`; review the diff before committing.
- python: a change under `scripts/` or `tools/energy/` passes `python3 -m pytest scripts/tests tools/energy/tests tools/quick-bench/tests`.
- python: a change to `scripts/pipeline.py` passes `python3 scripts/tests/test_manifest.py`.
- analysis: a change to `tools/quick-bench/*.py` passes `python3 tools/quick-bench/tests/test_analyze.py`; `-u` rewrites `tools/quick-bench/tests/golden_summary.md` and `golden_chart_summary.md`.
- perf-repair: a change under `perf-repair/` passes `make -C perf-repair check`.
- docs: a change to any guide or doc passes `python3 scripts/docs_lint.py`.
- ci: no workflow runs the Python tests or `make -C perf-repair check`; run them locally.
- fixtures: tests may name devices, providers and algorithms; main code may not.
