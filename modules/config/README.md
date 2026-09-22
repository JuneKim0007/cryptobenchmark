# Config

> An independent module that decides what a run will measure: what the device has, crossed with what the user asked for.

## Responsibilities

- Turn discovery's capture and trial into `inventory.yaml`: what this device runs, observations only.
- Cross the inventory with the authored `config/` (global settings and a test set) into `effective.yaml`.

  1. For more information, refer to <config.md>.

## File Structure

- `config/`
  - `build.gradle`
  - `README.md`
  - `docs/`
    - `config.md`
  - `example/`
    - `config_capture_example.yaml`
    - `config_effective_example.yaml`
    - `config_global_example.yaml`
    - `config_inventory_example.yaml`
    - `config_testset_example.yaml`
    - `config_trial_example.yaml`
  - `src/main/kotlin/`
    - `Configuration.kt`
    - `effective/`
      - `EffectiveBuilder.kt`
      - `EffectiveDocument.kt`
      - `LocatedMatch.kt`
      - `OverrideResolver.kt`
      - `StoppedOnFailureException.kt`
      - `dto/`
        - `EffectiveConfig.kt`
        - `EffectiveEntry.kt`
        - `EffectiveSource.kt`
        - `Skip.kt`
    - `global/`
      - `GlobalDocument.kt`
      - `PolicyDocument.kt`
      - `RunDocument.kt`
      - `dto/`
        - `GlobalConfig.kt`
        - `Policy.kt`
        - `RunSettings.kt`
        - `Selection.kt`
    - `inventory/`
      - `InventoryBuilder.kt`
      - `InventoryDocument.kt`
      - `dto/`
        - `Inventory.kt`
        - `InventoryEntry.kt`
        - `InventorySource.kt`
    - `source/`
      - `CaptureSource.kt`
      - `CaptureView.kt`
      - `TrialSource.kt`
      - `TrialView.kt`
    - `testset/`
      - `RuleDocument.kt`
      - `TestSetDocument.kt`
      - `dto/`
        - `Override.kt`
        - `Rule.kt`
        - `TestSet.kt`
    - `yaml/`
      - `DocumentFields.kt`
      - `DocumentHandler.kt`
      - `DocumentReader.kt`
      - `ProviderTree.kt`
      - `ReadOnlyYamlFile.kt`
      - `YamlCodec.kt`
      - `YamlFile.kt`
      - `YamlFiles.kt`
  - `src/test/kotlin/`
    - `ConfigurationTest.kt`
    - `DocumentsTest.kt`
    - `EffectiveBuilderTest.kt`
    - `ExampleFilesTest.kt`
    - `Fixtures.kt`
    - `InventoryBuilderTest.kt`
    - `OverrideResolverTest.kt`
    - `RuleTest.kt`

## Limitations

- The inventory is generated and always overwritten; the authored files under `config/` are never written by this module.
- An inventory describes one device at one moment: a test set names primitives, never providers of a given machine.
- A rule that matches nothing is a warning, not a failure: it may be legitimate on another device.

## Example

`example/` is one small device: capture, trial, global and test set in; inventory and effective out.
`ExampleFilesTest` runs both steps and compares the output with the committed files.
