# probe

Captures registered JCA providers and services, writes them as JSON, reduces them to a discovery setting.

Field contract: [security_contract.md](security_contract.md)

## Flow

```
Security.getProviders() -> ProviderProbe -> CapturedEnvironment -> EnvironmentYamlWriter     -> probe_<utc>.yaml
                                                               -> DiscoverySettingConverter -> DiscoverySetting
```

## JCA APIs used

| API | Gives |
|---|---|
| `Security.getProviders()` (caller) | providers, in preference order |
| `Provider.getName()`, `getVersion()`, `getInfo()` | provider identity |
| `Provider.getServices()` | type, algorithm, class name |
| `Provider.stringPropertyNames()`, `getProperty()` | aliases, attributes |

## Property keys

| Raw property | `PropertyKey` | Captured as |
|---|---|---|
| `Provider.id name` | `ProviderMeta` | skipped |
| `Alg.Alias.Cipher.RC4` = `ARC4` | `Alias` | alias on target service |
| `Cipher.AES SupportedModes` = `ECB\|CBC` | `Attribute` | typed attribute |
| `Cipher.AES` | `ServiceImpl` | skipped; services come from `getServices()` |
| anything else | `Malformed` | dropped |

## Limits

- attributes are optional: `SupportedModes`, `SupportedPaddings`, `KeySize` often absent
- transformations resolved by fallback are not listed (`Cipher.AES` serves `AES/CBC/PKCS5Padding`)
- an alias is a name, not a separate implementation
- a registered service can still fail at `init` or `doFinal`
- not visible: native crypto via JNI, providers not registered in this process, hardware (StrongBox, AES acceleration)

## Classes

Kotlin under `src/main/kotlin/`. `internal` means module-only, not part of the API.

| Class | Package | Role |
|---|---|---|
| `ProviderProbe` | `adapter` | JCA → capture; joins services with aliases and attributes |
| `PropertyMapIndex` | `adapter` | one provider's property map → aliases, attributes — `internal` |
| `PropertyKeyParser` | `adapter` | decodes the property-map grammar — `internal` |
| `PropertyKey` | `adapter` | one decoded key, discarded after use — sealed, `internal` |
| `DeclaredAlias` | `adapter` | one alias as declared — `internal` |
| `AttributeKind` | `adapter` | attribute name → `LIST`, `INT`, `BOOL`, `STRING` — `internal` |
| `AttributeValueParser` | `adapter` | attribute value → that type — `internal` |
| `DeviceRuntimeReader` | `adapter` | `android.os.Build` → `RuntimeInfo`, reflectively |
| `CapturedEnvironment` | `contract` | one capture |
| `ProviderEntry` | `contract` | one provider |
| `ServiceEntry` | `contract` | one service |
| `AliasEntry` | `contract` | one alias that resolved to nothing |
| `ServiceAttributes` | `contract` | typed attribute accessors |
| `RuntimeInfo` | `contract` | device and runtime provenance |
| `ServiceKey` | `contract` | `(type, algorithm)` key, `Locale.ROOT` folding — `internal` |
| `DiscoverySettingConverter` | `setting` | capture → setting |
| `BenchmarkScope` | `setting` | the 7 engine types measured |
| `DiscoverySetting` | `setting` | reduced setting; `providersFor`, `algorithms` |
| `ProviderSetting`, `ServiceSetting`, `Device` | `setting` | the reduced data |
| `ServiceLookup` | `setting` | find by name or alias — `internal` |
| `CaptureDocument` | `write` | the YAML schema: key names and capture → document |
| `EnvironmentYamlWriter` | `write` | document → `probe_<utc>.yaml` |
| `ProviderClassNameWriter` | `write` | provider → implementing class names, `probe_classes_<utc>.yaml` |
| `YamlDocument` | `write` | document → YAML text — `internal` |
| `ProbeFile` | `write` | timestamped name, directory, write — `internal` |

## Drift alarm

`src/test/kotlin/JcaContractTest.kt` asserts the limits above against the running JVM. The
`jca contract` workflow runs it weekly on Java 17, 21 and 25 and attaches each capture. A
failure means the JCA moved. Android providers are not covered (#14).

## Not yet

| Missing | Issue |
|---|---|
| read a capture back | #21 |
| verify services by trial | #15 |
| run as an independent process | #16 |
