# Config

> Turns what environment found into a file the user edits: `results/configuration/default.yaml`.

Reads environment's `probe_<utc>.yaml` and `trial_<utc>.yaml` as plain YAML; depends on no other module.

## File Structure

- `config/`
  - `build.gradle`
  - `README.md`
  - `docs/`
    - `config.md`
  - `src/main/kotlin/`
    - `Configuration.kt`
    - `source/`
      - `CaptureSource.kt`
      - `CaptureView.kt`
      - `TrialSource.kt`
      - `TrialView.kt`
    - `contract/`
      - `BenchmarkConfig.kt`
      - `GeneratedFrom.kt`
      - `RunSettings.kt`
      - `ConfigEntry.kt`
    - `generate/`
      - `DefaultConfigBuilder.kt`
      - `RunDefaults.kt`
    - `write/`
      - `ConfigDocument.kt`
      - `ConfigFile.kt`
      - `DocumentFields.kt`
      - `YamlCodec.kt`
  - `src/test/kotlin/`
    - `Fixtures.kt`
    - `DefaultConfigBuilderTest.kt`
    - `ConfigDocumentTest.kt`
    - `ConfigurationTest.kt`

## Run

`cd tools/jca-contract && ./gradlew run --args=../../results/discovery` writes the environment files and `results/configuration/default.yaml`.
