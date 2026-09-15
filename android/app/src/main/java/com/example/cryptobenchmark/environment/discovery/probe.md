# probe

Captures which cryptographic providers and services are registered in the running process, writes
the result as JSON, and reduces it to the discovery setting the benchmark uses.

Package: `com.example.cryptobenchmark.environment.discovery`
Field-level contract: [security_contract.md](security_contract.md)

---

## What it does

```
Security.getProviders() -> ProviderProbe -> CapturedEnvironment -> EnvironmentJsonWriter      -> JSON
   (caller)                reads the JCA     full capture          \
                                                                    DiscoverySettingConverter -> DiscoverySetting
                                                                    reduces                      what the benchmark needs
```

- The caller passes the provider array. `ProviderProbe` never calls `Security` itself, so it can be
  tested with hand-built providers.
- Pure `java.*`. No Android, no JSON, no benchmark dependency — except `EnvironmentJsonWriter`,
  which uses `org.json`.

---

## Dependency on the Java Security API (JCA)

### APIs used

| API | Gives |
|---|---|
| `Security.getProviders()` *(caller)* | installed providers, in preference order |
| `Provider.getName()`, `getVersion()`, `getInfo()` | provider identity |
| `Provider.getServices()` | each service: `getType()`, `getAlgorithm()`, `getClassName()` |
| `Provider.stringPropertyNames()` + `getProperty()` | the raw property map — aliases and declared attributes |

### Why the property map, not `getServices()` alone

`getServices()` returns neither aliases nor attributes. Both live only in the property map.

| Raw property | Kind | Captured as |
|---|---|---|
| `Provider.id name` | `PROVIDER_META` | skipped — would otherwise become a bogus service type |
| `Alg.Alias.Cipher.RC4` = `ARC4` | `ALIAS` | alias on the target service |
| `Cipher.AES SupportedModes` = `ECB\|CBC` | `ATTRIBUTE` | typed list on the service |
| `Cipher.AES` | `SERVICE_IMPL` | the service |
| anything else | `MALFORMED` | dropped |

Classification: `PropertyKey.classify`. Attribute typing: `AttributeKind`.

### What the JCA guarantees

| Guarantee | Source |
|---|---|
| providers returned in preference order | `Security.getProviders()` javadoc |
| every registered service is listed | `Provider.getServices()` javadoc |
| aliases and attributes are optional | `Provider.Service` javadoc |

### What it does not guarantee

| Gap | Effect on a capture |
|---|---|
| attributes are optional | `SupportedModes` / `SupportedPaddings` / `KeySize` often absent |
| transformation fallback | a bare `Cipher.AES` also serves `AES/CBC/PKCS5Padding`, which is never listed |
| aliases are names, not implementations | `PKCS7Padding` and `PKCS5Padding` can be one class |
| registered is not working | a listed service can still throw at `init` or `doFinal` |

Verifying by trial is tracked in #15.

---

## What it cannot see

| Out of reach | Why |
|---|---|
| native crypto — libsodium, `ring`, OpenSSL via JNI | not JCA providers |
| a provider bundled in the APK but not registered | invisible until `Security.addProvider` |
| other processes' providers | registration is per process |
| hardware — StrongBox, AES acceleration | not a provider property |

---

## Classes

| Class | Role |
|---|---|
| `ProviderProbe` | reads the JCA into the capture model |
| `PropertyKey` | classifies raw property keys |
| `ServiceKey` | `(type, algorithm)` key; owns `Locale.ROOT` folding for the whole package |
| `AttributeKind` | attribute name → type (`LIST`, `INT`, `BOOL`, `STRING`) |
| `ServiceAttributes` | typed attribute accessors |
| `ServiceEntry` | one service: type, algorithm, class, aliases, attributes |
| `ProviderEntry` | one provider: name, version, precedence, usable, services, unresolved aliases |
| `CapturedEnvironment` | one capture: schema version, timestamp, runtime, providers |
| `RuntimeInfo` | device provenance; reads `android.os.Build` reflectively |
| `EnvironmentJsonWriter` | capture → JSON (`org.json`) |
| `DiscoverySettingConverter` | capture → setting: keeps in-scope types and the attributes that narrow the matrix |
| `DiscoverySetting` | the reduced setting, with lookup by name or alias (`providersFor`, `algorithms`) |

---

## Not yet

| Missing | Issue |
|---|---|
| reading a capture back | #21 |
| verifying services by trial | #15 |
| running as an independent process | #16 |
