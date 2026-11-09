# Code

## Calls
- `docs/architecture.md` : Gradle projects, project dependencies, languages, stage YAML contract, isolation build
- `docs/tools.md` : tools/ builds, commands and outputs

## Rules
- generality: module main code names no device, provider or algorithm; selection comes from `config/` and the recorded capture and trial; tests, fixtures and `config/` may name them.
- capability: probe a per-device difference, record it in the trial or facts, and select behaviour from the recorded value; never branch on a provider name.
- dependency: add no project dependency beyond the table in `docs/architecture.md`.
- dependency: `:jca` and `:settings` depend on no project; `:environment:discovery` depends only on `:jca`.
- contract: a stage reads another stage's output from its file (capture, trial, inventory, effective, prepared, benchmark.json), never through that stage's classes.
- shared code: a module compiles against another module's classes only through the handoff types below; widening a list is a reviewed change to this guide.
- shared code: `:environment:discovery` and `:preparation` use jca's `Attempt`, `ErrorText`; `:benchmark` and `:android` androidTest use jca's `Attempt`; it is the one catch rule (an Exception or LinkageError is a result, any other Error escapes), never copied.
- shared code: `:config` uses settings' `Facts`, `HarnessSettings`, `Metric`, `Unsupported`.
- shared code: `:preparation` uses settings' `HarnessSettings`, `Metric`.
- shared code: `:benchmark` uses preparation's `BenchmarkCase`, `Operation`, `PreparedCase`, `Invocations`, `Invocation`, and for `RunnablePlan` `Preparation`, `Listing`, `PreparationException`, `StoppedOnFailureException`, `PreparedFile`, `Skip`, `SkipFile`, `GlobalSettings`, `OnFailure`, `FailureText`, and settings' `HarnessSettings`, `EnergySettings`, `CpuSettings`, `Metric`.
- shared code: `:android` androidTest uses preparation's `Preparation`, `DiscoveryCapability`, `InteropRun`, `InteropPlanFile`, `InteropFile`, `Invocations`, `PreparedCase`, `Skip`, `BenchmarkCase`, `Operation`, `KeyPlanner`, `KeyRecipe`, `KeyMaterial`, `KeyMaterialGenerator`; benchmark's `MetricSamples`, `PlanCheck`, `RunnablePlan`, `Refusal`, `EnergyCapability`, `CaseSettings`, `CaseRuns`, `Energy`, `WindowMarker`; settings' `CpuSettings`, `Metric`; discovery's `Discovery`, `BundledInstaller`, `BundledProviders`, `ProviderFactory`, `ProbeDirectory`, `YamlCodec`.
- shared code: `tools/` drivers call module entry points and writers; they are not modules and carry no handoff list.
- timing: build keys, inputs and parameters in `:preparation`; the timed block calls only the prepared `Invocation`.
- android: code in discovery, settings, preparation and benchmark uses only APIs in `android.jar`; `tools/android-api-check` compiles it without the JDK.
- jvm: modules and tools target Java 17.
- package: package root is `io.github.junekim0007.cryptobench`.
- package: Kotlin sources under `apps/benchmark/modules/<m>/src/main/kotlin/` omit the package-root folders; `:android` keeps full package folders.
- java: Java sources mirror the full package as folders under `src/main/java/`.
- errors: messages start with a snake_case code: `<code>: <detail>`.
- examples: discovery, config, preparation and benchmark keep `example/<module>_<responsibility>_example.(yaml|json)` and a test that compares them with what the code writes.
- gradle: every Gradle build uses the one wrapper `apps/benchmark/gradlew`; run `apps/benchmark/cli` or a `tools/` build through `apps/benchmark/gradlew -p <dir>`.
- python: a new host dependency goes in the root `requirements.txt`, and in `apps/benchmark-runner/dependencies.py` when only some runs need it; `apps/benchmark-runner/energy/requirements.txt` and `requirements-manafa.txt` stay for a separate `--energy-python`.
- comments: none by default; a kept comment is at most two lines and names a non-obvious trap or constraint.
- comments: no KDoc or docstring essays, no author, date, ticket or changelog comments.
- comments: a change updates or deletes every comment it made untrue.

## Dependency rules
- rules: `tools/module-isolation/layers.yaml` holds the module edges, the handoff lists above, package cycles and forbidden package edges as data; a list change edits it and this guide together.
- check: `tools/module-isolation/architecture` checks the compiled module classes with ArchUnit; `tools/module-isolation/handoff_check.py` checks androidTest and cli sources; `.github/workflows/modules.yml` runs both.
- frozen: violations that predate the rules live in `tools/module-isolation/architecture/frozen/` and `tools/module-isolation/handoff-frozen.txt`; a new violation fails and never joins them.
- frozen: the stores only shrink: a fixed violation leaves its store in the same change (`-Darchunit.freeze.store.default.allowStoreUpdate=true`, `handoff_check.py --shrink`); both are empty by the end of H3.
