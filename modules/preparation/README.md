# Preparation

> An independent module that turns one `effective.yaml` into cases the harness can measure, before any timer starts.

## Responsibilities

- Read `effective.yaml` in order: the file, then the global settings, then the primitives.
- Resolve what was asked for against what the device has, and reject the rest by name.
- Build each case's key, input and parameters, and call every case once to prove it runs.

  1. For more information, refer to <prepare.md>.

## File Structure

- `preparation/`
  - `build.gradle`
  - `README.md`
  - `docs/`
    - `prepare.md`
  - `src/main/kotlin/`
    - `Preparation.kt`
    - `inbound/`
      - `InboundFile.kt`
      - `InboundDocument.kt`
    - `global/`
      - `GlobalReader.kt`
      - `GlobalSettings.kt`
      - `OnFailure.kt`
    - `primitive/`
      - `PrimitiveReader.kt`
    - `request/`
      - `BenchmarkRequest.kt`
      - `Selection.kt`
    - `measurement/`
      - `BenchmarkCase.kt`
      - `CaseName.kt`
      - `Operation.kt`
      - `Phase.kt`
      - `Metric.kt`
      - `EngineTypeName.kt`
    - `port/`
      - `DeviceCapability.kt`
      - `Availability.kt`
    - `adapter/`
      - `DiscoveryCapability.kt`
    - `resolve/`
      - `CaseResolver.kt`
      - `SelectionCheck.kt`
      - `SelectionExpander.kt`
      - `AxisRules.kt`
      - `AxisRule.kt`
      - `Resolution.kt`
      - `Rejection.kt`
    - `parameter/bind/`
      - `ParameterBinder.kt`
      - `ValueNode.kt`
      - `ValueCoercion.kt`
      - `BindPolicy.kt`
      - `BoundParameters.kt`
      - `BindException.kt`
    - `key/plan/`
      - `KeyPlanner.kt`
      - `KeyShapes.kt`
      - `KeyShape.kt`
      - `KeyAlgorithmName.kt`
      - `KeyCandidate.kt`
      - `KeyRecipe.kt`
    - `key/generate/`
      - `KeyMaterialGenerator.kt`
      - `KeyInitializer.kt`
      - `DefaultKeyInitializer.kt`
      - `KeyMaterial.kt`
    - `input/`
      - `InputPreparer.kt`
      - `InputBytes.kt`
      - `OperationInput.kt`
      - `CipherKeys.kt`
    - `check/`
      - `CaseCheck.kt`
    - `prepare/`
      - `PreparedCase.kt`
      - `PreparedRun.kt`
      - `StoppedOnFailureException.kt`
    - `report/`
      - `Skip.kt`
      - `SkipFile.kt`
    - `shared/`
      - `DocumentFields.kt`
      - `YamlCodec.kt`

## Limitations

- Preparation reads `effective.yaml` only. It never reads the configuration module's classes, and never probes the device itself.
- A case is proved by one call, not by a measurement: timing, warmup and iteration counts belong to the harness.
- `TYPE_DEFAULT` cases are not called: nothing here knows how to invoke an engine type it has no rule for.
