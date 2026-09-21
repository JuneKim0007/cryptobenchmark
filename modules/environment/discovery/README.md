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
    - `setting/`
      - `DiscoverySettingConverter.kt`
      - `BenchmarkScope.kt`
      - `DiscoverySetting.kt`
      - `ProviderSetting.kt`
      - `ServiceSetting.kt`
      - `Device.kt`
      - `ServiceLookup.kt`
    - `write/`
      - `EnvironmentYamlWriter.kt`
      - `ProviderClassNameWriter.kt`
      - `YamlDocument.kt`
      - `ProbeFile.kt`
  - `src/test/kotlin/`
    - `JcaContractTest.kt`
    - `ServiceKeyTest.kt`

## Limitations

- The `Probe` module primarily uses the Java Security library, particularly `java.security.Provider`, making it highly dependent on the Java Security API.
- `Probe` only searches for cryptography providers registered in Java. Unregistered cryptography algorithms and pr
