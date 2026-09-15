# probe

Captures which cryptographic providers and services are registered in the running process, and
writes the result as JSON.

Package: `com.example.cryptobenchmark.environment.discovery`

---

## What it does

```
Security.getProviders()  ->  ProviderProbe.capture(...)  ->  CapturedEnvironment  ->  EnvironmentJsonWriter
   (caller)                     reads the JCA                  the model                 JSON
```

- The caller passes the provider array. `ProviderProbe` never calls `Security` itself, so it can be
  tested with hand-built providers.
- Pure `java.*`. No Android, no JSON, no benchmark dependency.

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
| `ProviderProbe` | reads the JCA into the model |
| `PropertyKey` | classifies raw property keys |
| `ServiceKey` | `(type, algorithm)` key, folded with `Locale.ROOT` |
| `AttributeKind` | attribute name → type (`LIST`, `INT`, `BOOL`, `STRING`) |
| `ServiceAttributes` | typed attribute accessors |
| `ServiceEntry` | one service: type, algorithm, class, aliases, attributes |
| `ProviderEntry` | one provider: name, version, precedence, usable, services, unresolved aliases |
| `CapturedEnvironment` | one capture: schema version, timestamp, runtime, providers |
| `RuntimeInfo` | device provenance; reads `android.os.Build` reflectively |
| `EnvironmentJsonWriter` | model → JSON (`org.json`) |

---

## Output

```json
{
  "schemaVersion": 1,
  "capturedAtMillis": 0,
  "runtime": { "model": "", "manufacturer": "", "hardware": "", "sdkInt": 0, "release": "", "javaVersion": "" },
  "providers": [
    {
      "name": "AndroidOpenSSL", "version": "1.0", "precedence": 1, "info": "", "usable": true,
      "services": [
        { "type": "Cipher", "algorithm": "AES/GCM/NoPadding", "className": "…",
          "aliases": ["…"], "attributes": { "SupportedModes": ["…"] } }
      ],
      "unresolvedAliases": { "Cipher RC4": "ARC4" }
    }
  ]
}
```

- Services sorted by type, then algorithm; aliases sorted — two captures diff cleanly.
- `precedence` is the 1-based position in the array passed to `capture`.
- `usable` is false for a registered provider with no services.
- `aliases`, `attributes`, `unresolvedAliases` are omitted when empty.

---

## Not yet

| Missing | Issue |
|---|---|
| reading a capture back | #21 |
| verifying services by trial | #15 |
| running as an independent process | #16 |
