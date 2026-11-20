# Testing

## Calls
- `docs/architecture.md` : isolation build: which sources each module compiles with
- `docs/tools.md` : tools/ builds, commands and outputs

## Rules
- isolation: a change to jca, document, discovery, config, preparation or benchmark passes `apps/benchmark/gradlew -p tools/module-isolation :<m>:test` for each touched module (`files`, `jca`, `document`, `discovery`, `config`, `preparation`, `benchmark`).
- isolation: a module that needs another module's classes outside the table in `docs/architecture.md` fails here; fix the dependency, never the isolation build.
- contract: a change to document, discovery, settings or config passes `apps/benchmark/gradlew -p apps/benchmark/cli test`.
- android api: a change to files, jca, document, discovery, settings, preparation or benchmark passes `apps/benchmark/gradlew -p tools/android-api-check compileKotlin`; pass `-PandroidJar=<android.jar>` when `$ANDROID_HOME/platforms/android-36/android.jar` is absent.
- settings: a change to `:settings` passes `apps/benchmark/gradlew -p apps/benchmark :settings:test`.
- android: a change under `apps/benchmark/modules/android/` passes `apps/benchmark/gradlew -p apps/benchmark build :android:compileReleaseAndroidTestKotlin` (needs `ANDROID_HOME`).
- examples: regenerate committed `example/` files only after a schema change: `apps/benchmark/gradlew -p tools/module-isolation test -Dexamples.update=true`; review the diff before committing.
- names: a change to `apps/benchmark/modules/files/` or `lib/cryptobench/cryptobench/shared/paths/names.py` passes `python3 tools/module-isolation/names_check.py`.
- python env: the suites run in an interpreter with the root `requirements.txt` installed, as CI's `tests.yml` does (`python3 -m venv <dir>`, `<dir>/bin/pip install -r requirements.txt`): it holds `pytest`, `perfetto` (without it `apps/benchmark-runner/tests/test_parity_constants.py` does not collect) and this checkout's `lib/cryptobench` as an editable install.
- python: a change under `apps/benchmark-runner/`, `apps/cli/`, `lib/cryptobench/` or `tools/` passes `python3 -m pytest apps/benchmark-runner/tests apps/benchmark-runner/energy/tests apps/benchmark-runner/analysis/tests apps/cli/tests tools/tests lib/cryptobench/cryptobench`.
- layering: a change under `lib/cryptobench/` passes `python3 -m pytest tools/tests/test_lib_layers.py`; its `RULES` table says what each package must not import.
- error codes: a coded message added or changed in Python or a Kotlin main source passes `python3 -m pytest tools/tests/test_error_codes.py`; a new code gets its entry in `lib/cryptobench/cryptobench/shared/errors/codes.yaml`.
- python: a change to `lib/cryptobench/cryptobench/shared/results/`, `lib/cryptobench/cryptobench/shared/device/identity.py` or `lib/cryptobench/cryptobench/shared/device/capture.py` passes `python3 -m pytest apps/benchmark-runner/tests/test_manifest.py`.
- analysis: a change to `apps/benchmark-runner/analysis/*.py` passes `python3 -m pytest apps/benchmark-runner/analysis/tests/test_analyze.py`; `python3 apps/benchmark-runner/analysis/tests/test_analyze.py -u` rewrites `apps/benchmark-runner/analysis/tests/golden_summary.md` and `golden_chart_summary.md`.
- perf-repair: a change under `apps/perf-repair/` passes `make -C apps/perf-repair check`.
- docs: a change to any guide or doc passes `python3 tools/docs_lint.py`.
- ci: a Gradle or Python test command added here gets its step in `.github/workflows/tests.yml`.
- fixtures: tests may name devices, providers and algorithms; main code may not.
