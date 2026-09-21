# Config

> Environment's findings (`inventory.yaml`) × the user's authored `config/` (global + test set) → `effective.yaml`, what one run will measure.

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
    - `inventory/`
      - `InventoryBuilder.kt`
      - `InventoryDocument.kt`
      - `dto/`
        - `Inventory.kt`
        - `InventoryEntry.kt`
        - `InventorySource.kt`
    - `global/`
      - `GlobalDocument.kt`
      - `RunDocument.kt`
      - `PolicyDocument.kt`
      - `dto/`
        - `GlobalConfig.kt`
        - `Selection.kt`
        - `RunSettings.kt`
        - `Policy.kt`
    - `testset/`
      - `TestSetDocument.kt`
      - `RuleDocument.kt`
      - `dto/`
        - `TestSet.kt`
        - `Rule.kt`
        - `Override.kt`
    - `effective/`
      - `EffectiveBuilder.kt`
      - `OverrideResolver.kt`
      - `EffectiveDocument.kt`
      - `StoppedOnFailureException.kt`
      - `LocatedMatch.kt`
      - `dto/`
        - `EffectiveConfig.kt`
        - `EffectiveEntry.kt`
        - `EffectiveSource.kt`
        - `Skip.kt`
    - `yaml/`
      - `DocumentReader.kt`
      - `DocumentHandler.kt`
      - `ReadOnlyYamlFile.kt`
      - `YamlFile.kt`
      - `YamlFiles.kt`
      - `ProviderTree.kt`
      - `DocumentFields.kt`
      - `YamlCodec.kt`
  - `src/test/kotlin/`
    - `Fixtures.kt`
    - `InventoryBuilderTest.kt`
    - `RuleTest.kt`
    - `OverrideResolverTest.kt`
    - `EffectiveBuilderTest.kt`
    - `DocumentsTest.kt`
    - `ConfigurationTest.kt`

## Run

`cd tools/jca-contract && ./gradlew run --args=../../results/discovery` writes the environment files, `results/configuration/inventory.yaml` and `effective.yaml` (from `config/global.yaml`).
