# Preparation

> An independent module that turns one `effective.yaml` into cases the harness can measure, before any timer starts.

## Responsibilities

- Read `effective.yaml` in order: the file, then the global settings, then the primitives.
- Read the capture and trial for what the device serves, and reject what it cannot run by name.
- Build each case's key, input and parameters, and call every case once to prove it runs.

  1. For more information, refer to <prepare.md>.

## File Structure

- `preparation/`
  - `build.gradle`
  - `README.md`
  - `docs/`
    - `prepare.md`
  - `example/`
    - `preparation_capture_example.yaml`
    - `preparation_effective_example.yaml`
    - `preparation_skipped_example.yaml`
    - `preparation_trial_example.yaml`
  - `src/main/kotlin/`
    - `Preparation.kt`
    - `adapter/`
      - `DiscoveryCapability.kt`
    - `check/`
      - `CaseCheck.kt`
    - `device/`
      - `CaptureFile.kt`
      - `ServiceName.kt`
      - `TrialFile.kt`
      - `dto/`
        - `CapturedDevice.kt`
        - `CapturedProvider.kt`
        - `CapturedService.kt`
        - `TrialledDevice.kt`
        - `TrialledService.kt`
        - `TrialledTransformation.kt`
    - `engine/`
      - `CaseEngines.kt`
      - `EngineType.kt`
      - `EngineTypes.kt`
      - `KeyShape.kt`
    - `global/`
      - `GlobalReader.kt`
      - `GlobalSettings.kt`
      - `OnFailure.kt`
    - `inbound/`
      - `InboundDocument.kt`
      - `InboundFile.kt`
    - `input/`
      - `CipherKeys.kt`
      - `InputBytes.kt`
      - `InputPreparer.kt`
      - `OperationInput.kt`
    - `key/`
      - `generate/`
        - `DefaultKeyInitializer.kt`
        - `KeyInitializer.kt`
        - `KeyMaterial.kt`
        - `KeyMaterialGenerator.kt`
      - `plan/`
        - `KeyAlgorithmName.kt`
        - `KeyCandidate.kt`
        - `KeyPlanner.kt`
        - `KeyRecipe.kt`
    - `measurement/`
      - `BenchmarkCase.kt`
      - `CaseName.kt`
      - `EngineTypeName.kt`
      - `Metric.kt`
      - `Operation.kt`
      - `Phase.kt`
    - `parameter/`
      - `bind/`
        - `BindException.kt`
        - `BindPolicy.kt`
        - `BoundParameters.kt`
        - `ParameterBinder.kt`
        - `ValueCoercion.kt`
        - `ValueNode.kt`
    - `port/`
      - `Availability.kt`
      - `DeviceCapability.kt`
    - `prepare/`
      - `PreparedCase.kt`
      - `PreparedRun.kt`
      - `StoppedOnFailureException.kt`
    - `primitive/`
      - `PrimitiveReader.kt`
    - `report/`
      - `Skip.kt`
      - `SkipFile.kt`
    - `request/`
      - `BenchmarkRequest.kt`
      - `Selection.kt`
    - `resolve/`
      - `CaseResolver.kt`
      - `Rejection.kt`
      - `Resolution.kt`
      - `SelectionCheck.kt`
      - `SelectionExpander.kt`
    - `shared/`
      - `DocumentFields.kt`
      - `YamlCodec.kt`
  - `src/test/kotlin/`
    - `BenchmarkCaseTest.kt`
    - `BenchmarkRequestTest.kt`
    - `CaseResolverTest.kt`
    - `DiscoveryCapabilityTest.kt`
    - `EffectiveFixture.kt`
    - `EngineTypesTest.kt`
    - `ExampleFilesTest.kt`
    - `GlobalReaderTest.kt`
    - `InboundFileTest.kt`
    - `InputPreparerTest.kt`
    - `KeyAlgorithmNameTest.kt`
    - `KeyMaterialGeneratorTest.kt`
    - `KeyPlannerTest.kt`
    - `ParameterBinderTest.kt`
    - `PreparationTest.kt`
    - `PrimitiveReaderTest.kt`

## Limitations

- Reads YAML only: `effective.yaml`, the capture and the trial. It never probes the device itself.
- A case is proved by one call, not by a measurement: timing, warmup and iteration counts belong to the harness.
- `TYPE_DEFAULT` cases are not called: nothing here knows how to invoke an engine type it has no rule for.

## Example

`example/` is one small device: capture, trial and effective in; skipped out.
`ExampleFilesTest` prepares every case against the running JVM and compares `skipped` with the committed file.
