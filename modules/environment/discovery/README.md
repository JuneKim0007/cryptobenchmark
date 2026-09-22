# Discovery

> An independent module designed to discover available settings and device capabilities within scope.

## Responsibilities

- Discovery is responsible for identifying available cryptography providers.

  1. For more information, refer to <probe.md>.

## File Structure
> File structure + their responsibilities. For potential ambiguity, I've prepared documents for each components. 


- `discovery/`
  - `build.gradle`
  - `README.md`
  - `docs/`
    - `probe.md`
    - `security_contract.md`
  - `src/main/kotlin/`
    - `Discovery.kt`
    - `DiscoveryRun.kt`
    - `ReusedRun.kt`
    - `adapter/`
      - `ProviderProbe.kt`
      - `PropertyMapIndex.kt`
      - `PropertyKeyParser.kt`
      - `PropertyKey.kt`
      - `DeclaredAlias.kt`
      - `AttributeKind.kt`
      - `AttributeValueParser.kt`
      - `DeviceRuntimeReader.kt`
    - `contract/`
      - `CapturedEnvironment.kt`
      - `ProviderEntry.kt`
      - `ServiceEntry.kt`
      - `AliasEntry.kt`
      - `ServiceAttributes.kt`
      - `RuntimeInfo.kt`
      - `ServiceKey.kt`
      - `ServiceKeyException.kt`
      - `TrialReport.kt`
      - `ServiceTrialEntry.kt`
      - `TransformationTrialEntry.kt`
      - `TrialOutcome.kt`
      - `DefaultRunOutcome.kt`
    - `query/`
      - `CaptureQuery.kt`
      - `TrialQuery.kt`
      - `ServiceShape.kt`
      - `TransformationFailure.kt`
      - `ServiceIndex.kt`
      - `ServiceTree.kt`
    - `trial/`
      - `TrialRunner.kt`
      - `Attempt.kt`
      - `TransformationSet.kt`
      - `DefaultRunTrial.kt`
      - `call/`
        - `DefaultCall.kt`
        - `DefaultCalls.kt`
        - `CipherCall.kt`
        - `SignatureCall.kt`
        - `MacCall.kt`
        - `DigestCall.kt`
        - `GeneratorCall.kt`
        - `AgreementCall.kt`
        - `DefaultKeys.kt`
        - `KeyNames.kt`
        - `KeyBits.kt`
    - `write/`
      - `CaptureDocument.kt`
      - `DocumentFields.kt`
      - `EnvironmentYamlWriter.kt`
      - `ProviderClassNameWriter.kt`
      - `TrialDocument.kt`
      - `TrialYamlWriter.kt`
      - `YamlCodec.kt`
      - `ProbeDirectory.kt`
      - `ProbeFileName.kt`
  - `src/test/kotlin/`
    - `JcaContractTest.kt`
    - `CaptureDocumentTest.kt`
    - `ProviderProbeTest.kt`
    - `ProbeDirectoryTest.kt`
    - `YamlCodecTest.kt`
    - `TrialRunnerTest.kt`
    - `TrialDocumentTest.kt`
    - `CaptureQueryTest.kt`
    - `TrialQueryTest.kt`
    - `ServiceKeyTest.kt`

## Limitations

- The `Probe` module primarily uses the Java Security library, particularly `java.security.Provider`, making it highly dependent on the Java Security API.
- `Probe` only searches for cryptography providers registered in Java. Unregistered cryptography algorithms and pr

## Example

`example/` holds one small device, in the files this module reads and writes:

- `discovery_capture_example.yaml`
- `discovery_trial_example.yaml`

`tools/module-isolation` compiles this module alone — no other module on the classpath — and runs its
tests from this directory against those files. Regenerate the generated ones with `-Dexamples.update`.
