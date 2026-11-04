# Code

## Calls
- `docs/architecture.md` : Gradle projects, project dependencies, languages, stage YAML contract, isolation build
- `docs/tools.md` : tools/ builds, commands and outputs

## Rules
- generality: module main code names no device, provider or algorithm; selection comes from `config/` and the recorded capture and trial; tests, fixtures and `config/` may name them.
- capability: probe a per-device difference, record it in the trial or facts, and select behaviour from the recorded value; never branch on a provider name.
- dependency: add no project dependency beyond the table in `docs/architecture.md`.
- dependency: `:environment:discovery` and `:settings` depend on no project.
- contract: a stage reads another stage's output from its file (capture, trial, inventory, effective, prepared, benchmark.json), never through that stage's classes.
- shared code: a module compiles against another module's classes only through the handoff types below; widening a list is a reviewed change to this guide.
- shared code: `:config` uses settings' `Facts`, `HarnessSettings`, `Metric`, `Unsupported`.
- shared code: `:preparation` uses settings' `HarnessSettings`, `Metric`.
- shared code: `:benchmark` uses preparation's `BenchmarkCase`, `Operation`, `PreparedCase`, `PreparedRun`, `Invocations`, `Invocation`, `KeyRecipe`, and settings' `HarnessSettings`, `EnergySettings`, `CpuSettings`, `Metric`.
- shared code: `:android` androidTest uses preparation's `Preparation`, `DiscoveryCapability`, `GlobalReader`, `InboundFile`, `InteropRun`, `InteropPlanFile`, `InteropFile`, `Invocations`, `PreparedCase`, `PreparedFile`, `Skip`, `SkipFile`; benchmark's `PlanCheck`, `Refusal`, `EnergyCapability`, `RefusedPlanException`, `CaseSettings`, `CaseRuns`, `Energy`, `WindowMarker`; settings' `CpuSettings`, `Metric`; discovery's `Discovery`, `BundledInstaller`, `BundledProviders`, `ProviderFactory`, `ProbeDirectory`, `YamlCodec`.
- shared code: `tools/` drivers call module entry points and writers; they are not modules and carry no handoff list.
- timing: build keys, inputs and parameters in `:preparation`; the timed block calls only the prepared `Invocation`.
- android: code in discovery, settings, preparation and benchmark uses only APIs in `android.jar`; `tools/android-api-check` compiles it without the JDK.
- jvm: modules and tools target Java 17.
- package: package root is `io.github.junekim0007.cryptobench`.
- package: Kotlin sources under `modules/<m>/src/main/kotlin/` omit the package-root folders; `:android` keeps full package folders.
- java: Java sources mirror the full package as folders under `src/main/java/`.
- errors: messages start with a snake_case code: `<code>: <detail>`.
- examples: discovery, config, preparation and benchmark keep `example/<module>_<responsibility>_example.(yaml|json)` and a test that compares them with what the code writes.
- gradle: every Gradle build uses the root wrapper; run a `tools/` build through `./gradlew -p <dir>`.
- python: a new host dependency goes in the root `requirements.txt`, and in `scripts/dependencies.py` when only some runs need it; `tools/energy/requirements.txt` and `requirements-manafa.txt` stay for a separate `--energy-python`.
- comments: none by default; a kept comment is at most two lines and names a non-obvious trap or constraint.
- comments: no KDoc or docstring essays, no author, date, ticket or changelog comments.
- comments: a change updates or deletes every comment it made untrue.
