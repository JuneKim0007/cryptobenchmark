# <config>

`default.yaml`: provider → engine type → name → entry. Generated from one capture and its trial; always overwritten (#34).

## Flow

```
probe_<utc>.yaml ─► CaptureSource ─► CaptureView ─┐
trial_<utc>.yaml ─► TrialSource   ─► TrialView  ──┴─► DefaultConfigBuilder ─► BenchmarkConfig ─► ConfigDocument ─► default.yaml
```

## Fields

| Key | Type | Written when | Meaning |
|---|---|---|---|
| `schemaVersion` | int | always | 1 |
| `generatedFrom.capture`, `.trial` | string | always | environment file names |
| `generatedFrom.device` | map | always | capture `runtime` block |
| `run.inputSizes` | [int] | always | bytes per call, every entry |
| `run.phases` | [string] | always | `WARM`, `COLD` |
| `run.metrics` | [string] | always | `TIME`, `ALLOCATION`, `CPU_EVENTS` |
| `run.processRepetitions` | int | always | independent process runs |
| `run.seed` | int | always | input seed |
| `<provider>.<type>.<name>.enabled` | bool | always | user switch; generated `true` exactly when the default run worked |
| `.keySizes` | [int] | a key size was observed | generated: the provider's default |
| `.inputSizes` | [int] | the default run needed another size | overrides `run.inputSizes` (RSA: 32) |
| `.keyAlgorithm`, `.keyProvider` | string | a key was generated | what the default run used |
| `.providerChose` | string | a cipher filled in parameters | IV length, OAEP digests; recorded, not configurable |
| `.bareName` | bool | a cipher name without mode | the provider's default mode and padding |
| `.reason` | string | the default run failed | the exception |
| `.key` | tree | the user sets it | key generator spec, e.g. `{class: java.security.spec.ECGenParameterSpec, arguments: [secp256r1]}`; replaces `keySizes` |
| `.parameters` | tree | the user sets it | operation spec, e.g. `{class: javax.crypto.spec.GCMParameterSpec, arguments: [128, fresh(12)]}`; absent = provider default |

## Parameter trees

`key` and `parameters` are passed through untouched here and bound by preparation.

| Form | Means |
|---|---|
| `{class: <fully qualified name>, arguments: [...]}` | public constructor, tried in turn for the argument count |
| `{field: <fully qualified class>.<NAME>}` | public static field, e.g. `java.security.spec.MGF1ParameterSpec.SHA256` |
| `fresh(n)` | n new random bytes on every call (a GCM IV must never repeat) |
| `!!binary <base64>` or `[0, 1, 255]` | `byte[]` |
| a number | `int`, `long` or `BigInteger`, whichever the constructor takes |

Only subtypes of `AlgorithmParameterSpec`, `PSource` and `BigInteger` may be named. A failure names its path: `bind_failed: parameters.arguments[2]: no public field ...`.

## Rules

- entries: every name environment called with a default key; instantiation alone is not an entry
- names are compared ignoring case; two spellings of one name under one provider and type are rejected
- a key written twice is rejected, not overwritten
- a trial of another capture is rejected

## Provider-specific, observed on JDK 25

| Observation | Handling |
|---|---|
| spelling chosen by provider (`AES/CBC/PKCS5PADDING`) | names compared ignoring case |
| size inside the name (`AES_128/GCM/NoPadding`) | `keySizes` observed from the name |
| default key sizes differ (RSA 3072, EC 384, DH 3072) | written as numbers, never left implicit |
| no size at all (Ed25519, X25519, ML-DSA-*) | `keySizes` absent |
| input limits (RSA, `NONEwithDSA` 20 bytes) | `inputSizes` per entry |
| needs parameters not modelled (PBE, RSASSA-PSS, `SunTls*`) | disabled with `reason` |
| no two providers serve the same name on the JVM | cross-provider behaviour unverified until a device run (#14) |
