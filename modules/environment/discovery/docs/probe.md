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
| `ProviderProbe` | `probe` | JCA → capture; normalises null and ordering |
| `PropertyKeyParser` | `probe` | decodes the property-map grammar — `internal` |
| `PropertyKey` | `probe` | one decoded key, discarded after use — sealed, `internal` |
| `AttributeKind` | `probe` | attribute name → `LIST`, `INT`, `BOOL`, `STRING` — `internal` |
| `CapturedEnvironment` | `capture` | one capture |
| `ProviderEntry` | `capture` | one provider |
| `ServiceEntry` | `capture` | one service |
| `ServiceAttributes` | `capture` | typed attribute accessors |
| `RuntimeInfo` | `capture` | device and runtime provenance |
| `DiscoverySettingConverter` | `setting` | capture → setting |
| `DiscoverySetting` | `setting` | reduced setting; `providersFor`, `algorithms` |
| `ServiceKey` | root | `(type, algorithm)` key, `Locale.ROOT` folding — `internal` |
| `EnvironmentYamlWriter` | `write` | capture → YAML file |

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
