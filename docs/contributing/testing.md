# Testing

## Calls
- `docs/architecture.md` : isolation build: which sources each module compiles with
- `docs/tools.md` : tools/ builds, commands and outputs

## Rules
- isolation: a change to discovery, config, preparation or benchmark passes `apps/benchmark/gradlew -p tools/module-isolation :<m>:test` for each touched module (`discovery`, `config`, `preparation`, `benchmark`).
- isolation: a module that needs another module's classes outside the table in `docs/architecture.md` fails here; fix the dependency, never the isolation build.
- contract: a change to discovery, settings or config passes `apps/benchmark/gradlew -p apps/benchmark/cli test`.
- android api: a change to discovery, settings, preparation or benchmark passes `apps/benchmark/gradlew -p tools/android-api-check compileKotlin`; pass `-PandroidJar=<android.jar>` when `$ANDROID_HOME/platforms/android-36/android.jar` is absent.
- settings: a change to `:settings` passes `apps/benchmark/gradlew -p apps/benchmark :settings:test`.
- android: a change under `apps/benchmark/modules/android/` passes `apps/benchmark/gradlew -p apps/benchmark build :android:compileReleaseAndroidTestKotlin` (needs `ANDROID_HOME`).
- examples: regenerate committed `example/` files only after a schema change: `apps/benchmark/gradlew -p tools/module-isolation test -Dexamples.update=true`; review the diff before committing.
- python: a change under `apps/benchmark-runner/` or `apps/cli/` passes `python3 -m pytest apps/benchmark-runner/tests apps/benchmark-runner/energy/tests apps/benchmark-runner/analysis/tests apps/cli/tests`.
- python: a change to `apps/benchmark-runner/results/` `apps/benchmark-runner/device/identity.py` or `apps/benchmark-runner/device/capture.py` passes `python3 apps/benchmark-runner/tests/test_manifest.py`.
- analysis: a change to `apps/benchmark-runner/analysis/*.py` passes `python3 apps/benchmark-runner/analysis/tests/test_analyze.py`; `-u` rewrites `apps/benchmark-runner/analysis/tests/golden_summary.md` and `golden_chart_summary.md`.
- perf-repair: a change under `apps/perf-repair/` passes `make -C apps/perf-repair check`.
- docs: a change to any guide or doc passes `python3 tools/docs_lint.py`.
- ci: a Gradle or Python test command added here gets its step in `.github/workflows/tests.yml`.
- fixtures: tests may name devices, providers and algorithms; main code may not.
