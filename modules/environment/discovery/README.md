# Discovery

> An independent module designed to discover available settings and device capabilities within scope.

## Responsibilities

- Identify the cryptography providers and services this device registers, and what each declares.
- Call every service once, then once more with a default key, and record what really runs.

  1. For more information, refer to <probe.md>. Field tables: <security_contract.md>.

## File Structure
> File structure + their responsibilities. For potential ambiguity, I've prepared documents for each components.

- `discovery/`
  - `build.gradle`
  - `README.md`
  - `docs/`
    - `probe.md`
    - `security_contract.md`
    - `tree.md`
  - `example/`
    - `discovery_capture_example.yaml`
    - `discovery_trial_example.yaml`
  - `src/main/kotlin/`
    - `Discovery.kt`
    - `DiscoveryRun.kt`
    - `ReusedRun.kt`
    - `adapter/`
      - `AttributeKind.kt`
      - `AttributeValueParser.kt`
      - `DeclaredAlias.kt`
      - `DeviceRuntimeReader.kt`
      - `PropertyKey.kt`
      - `PropertyKeyParser.kt`
      - `PropertyMapIndex.kt`
      - `ProviderProbe.kt`
    - `contract/`
      - `AliasEntry.kt`
      - `CapturedEnvironment.kt`
      - `DefaultRunOutcome.kt`
      - `ProviderEntry.kt`
      - `RuntimeInfo.kt`
      - `ServiceAttributes.kt`
      - `ServiceEntry.kt`
      - `ServiceKey.kt`
      - `ServiceKeyException.kt`
      - `ServiceTrialEntry.kt`
      - `TransformationTrialEntry.kt`
      - `TrialOutcome.kt`
      - `TrialReport.kt`
    - `query/`
      - `CaptureQuery.kt`
      - `ServiceIndex.kt`
      - `ServiceShape.kt`
      - `ServiceTree.kt`
      - `TransformationFailure.kt`
      - `TrialQuery.kt`
    - `trial/`
      - `Attempt.kt`
      - `DefaultRunTrial.kt`
      - `TransformationSet.kt`
      - `TrialRunner.kt`
      - `call/`
        - `AgreementCall.kt`
        - `CipherCall.kt`
        - `DefaultCall.kt`
        - `DefaultCalls.kt`
        - `DefaultKeys.kt`
        - `DigestCall.kt`
        - `GeneratorCall.kt`
        - `KeyBits.kt`
        - `KeyNames.kt`
        - `MacCall.kt`
        - `SignatureCall.kt`
    - `write/`
      - `CaptureDocument.kt`
      - `DocumentFields.kt`
      - `EnvironmentYamlWriter.kt`
      - `ProbeDirectory.kt`
      - `ProbeFileName.kt`
      - `ProviderClassNameWriter.kt`
      - `TrialDocument.kt`
      - `TrialYamlWriter.kt`
      - `YamlCodec.kt`
  - `src/test/kotlin/`
    - `CaptureDocumentTest.kt`
    - `CaptureQueryTest.kt`
    - `DefaultRunTrialTest.kt`
    - `ExampleFilesTest.kt`
    - `JcaContractTest.kt`
    - `KeyNamesTest.kt`
    - `ProbeDirectoryTest.kt`
    - `ProviderProbeTest.kt`
    - `ReuseTest.kt`
    - `ServiceAttributesTest.kt`
    - `ServiceKeyTest.kt`
    - `TrialDocumentTest.kt`
    - `TrialQueryTest.kt`
    - `TrialRunnerTest.kt`
    - `YamlCodecTest.kt`

## Limitations

- Depends on `java.security.Provider`: it sees only what a provider registers and declares.
- Unregistered implementations, native code behind JNI and hardware (StrongBox, AES acceleration) are invisible.

## Example

`example/` is one small device in the two files this module writes; `ExampleFilesTest` round-trips them.
Runnable over a live JVM from `tools/jca-contract`: `examples.TreeKt` (writes `docs/tree.md`) and
`examples.ReportKt` (every `CaptureQuery` and `TrialQuery` question).

```
./gradlew run -q -PmainClass=examples.ReportKt --args="Cipher AES SunJCE"
```
