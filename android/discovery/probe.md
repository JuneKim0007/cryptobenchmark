# probe

Captures registered JCA providers and services, writes them as JSON, reduces them to a discovery setting.

Field contract: [security_contract.md](security_contract.md)

## Flow

```
Security.getProviders() -> ProviderProbe -> CapturedEnvironment -> EnvironmentJsonWriter     -> JSON
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

Kotlin, flat in `src/main/kotlin/`. `internal` means module-only, not part of the API.

| Class | Role |
|---|---|
| `ProviderProbe` | JCA → capture; normalises null and ordering |
| `PropertyKey` | classifies property keys — sealed, `internal` |
| `ServiceKey` | `(type, algorithm)` key, `Locale.ROOT` folding — `internal` |
| `AttributeKind` | attribute name → `LIST`, `INT`, `BOOL`, `STRING` — `internal` |
| `ServiceAttributes` | typed attribute accessors |
| `ServiceEntry` | one service |
| `ProviderEntry` | one provider |
| `CapturedEnvironment` | one capture |
| `RuntimeInfo` | device and runtime provenance |
| `EnvironmentJsonWriter` | capture → JSON |
| `DiscoverySettingConverter` | capture → setting |
| `DiscoverySetting` | reduced setting; `providersFor`, `algorithms` |

## Not yet

| Missing | Issue |
|---|---|
| read a capture back | #21 |
| verify services by trial | #15 |
| run as an independent process | #16 |
