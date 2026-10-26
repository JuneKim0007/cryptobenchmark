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
- shared code: `:settings` (harness keys) and preparation's `Invocation` (used by `:benchmark`) are the only module classes another module compiles against.
- timing: build keys, inputs and parameters in `:preparation`; the timed block calls only the prepared `Invocation`.
- android: code in discovery, settings, preparation and benchmark uses only APIs in `android.jar`; `tools/android-api-check` compiles it without the JDK.
- jvm: modules and tools target Java 17.
- package: package root is `io.github.junekim0007.cryptobench`.
- package: Kotlin sources under `modules/<m>/src/main/kotlin/` omit the package-root folders; `:android` keeps full package folders.
- java: Java sources mirror the full package as folders under `src/main/java/`.
- errors: messages start with a snake_case code: `<code>: <detail>`.
- examples: discovery, config, preparation and benchmark keep `example/<module>_<responsibility>_example.(yaml|json)` and a test that compares them with what the code writes.
- gradle: run every `tools/` build through `tools/jca-contract/gradlew -p <dir>`.
- python: host scripts use the stdlib, PyYAML and matplotlib (`scripts/requirements.txt`); `tools/energy` adds `perfetto` (`tools/energy/requirements.txt`); a new dependency goes in the matching requirements file.
- comments: none by default; a kept comment is at most two lines and names a non-obvious trap or constraint.
- comments: no KDoc or docstring essays, no author, date, ticket or changelog comments.
- comments: a change updates or deletes every comment it made untrue.
