# Config

> An independent module that decides what a run will measure: what the device has, crossed with what the user asked for.

## Responsibilities

- Turn environment's capture and trial into `inventory.yaml`: what this device runs, observations only.
- Cross the inventory with the authored `config/` (global settings and a test set) into `effective.yaml`.

  1. For more information, refer to <config.md>.

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
      - `LocatedMatch.kt`
      - `StoppedOnFailureException.kt`
      - `dto/`
        - `EffectiveConfig.kt`
        - `EffectiveEntry.kt`
        - `EffectiveSource.kt`
        - `Skip.kt`
    - `yaml/`
      - `YamlFiles.kt`
      - `YamlFile.kt`
      - `ReadOnlyYamlFile.kt`
      - `DocumentHandler.kt`
      - `DocumentReader.kt`
      - `ProviderTree.kt`
      - `DocumentFields.kt`
      - `YamlCodec.kt`

## Limitations

- The inventory is generated and always overwritten; the authored files under `config/` are never written by this module.
- An inventory describes one device at one moment: a test set names primitives, never providers of a given machine.
- A rule that matches nothing is a warning, not a failure: it may be legitimate on another device.

## Example

`example/` holds one small device, in the files this module reads and writes:

- `config_capture_example.yaml`
- `config_trial_example.yaml`
- `config_global_example.yaml`
- `config_testset_example.yaml`
- `config_inventory_example.yaml`
- `config_effective_example.yaml`

`tools/module-isolation` compiles this module alone — no other module on the classpath — and runs its
tests from this directory against those files. Regenerate the generated ones with `-Dexamples.update`.
