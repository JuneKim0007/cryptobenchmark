# security_contract

Fields of the two files discovery writes: `probe_<utc>.yaml` (key names on `CaptureDocument`) and
`trial_<utc>.yaml` (key names on `TrialDocument`). Each `parse` rejects any other `schemaVersion`.
Config and preparation read these files, never these classes.

## capture

| Field | Type | Description |
|---|---|---|
| `schemaVersion` | int | capture format version |
| `capturedAtMillis` | long | capture time, epoch milliseconds |
| `runtime` | object | device the capture was taken on |
| `providers` | list | installed providers, in preference order |

## runtime

| Field | Type | Description |
|---|---|---|
| `model` | string | device model |
| `manufacturer` | string | device manufacturer |
| `hardware` | string | hardware name |
| `sdkInt` | int | Android API level |
| `release` | string | Android version |
| `javaVersion` | string | Java runtime version |
| `defaultKeySizeProperty` | string | system property `jdk.security.defaultKeySize`; overrides provider default key sizes; `''` when unset or absent (older captures) |

## providers[]

| Field | Type | Description |
|---|---|---|
| `name` | string | provider name |
| `version` | string | provider version |
| `precedence` | int | 1-based position in the search order |
| `info` | string | provider description |
| `usable` | bool | false when the provider registers no services |
| `services` | list | services the provider registers |
| `unresolvedAliases` | list | aliases whose target service is not registered, each `{type, alias, target}`; omitted when empty |

## services[]

| Field | Type | Description |
|---|---|---|
| `type` | string | service type, e.g. `Cipher`, `MessageDigest` |
| `algorithm` | string | algorithm name, e.g. `AES/GCM/NoPadding` |
| `className` | string | implementing class |
| `aliases` | list | alternate names for this service; omitted when empty |
| `attributes` | map | declared attributes; omitted when empty |

## attributes

| Field | Type | Description |
|---|---|---|
| `SupportedModes` | list | cipher modes |
| `SupportedPaddings` | list | cipher paddings |
| `SupportedKeyClasses` | list | accepted key classes |
| `SupportedKeyFormats` | list | accepted encoded key formats |
| `SupportedCurves` | list | supported elliptic curves |
| `KeySize` | int | largest supported key size; kept as the raw string when it does not parse |
| `ThreadSafe` | bool | implementation is thread safe |
| `ImplementedIn` | string | `Software` or `Hardware` |
| `MechanismType` | string | mechanism type |
| *any other* | string | vendor attribute, kept raw |

## trial

| Field | Type | Description |
|---|---|---|
| `schemaVersion` | int | trial format version, `2` |
| `capturedAtMillis` | long | the capture this trial belongs to; a mismatch is refused |
| `defaultRunInputSize` | int | the input size every default run tries first; absent in trials without default runs |
| `services` | list | one entry per captured service |

## services[] (trial)

| Field | Type | Description |
|---|---|---|
| `provider`, `type`, `algorithm` | string | the service |
| `instantiates` | bool | `getInstance` succeeded |
| `error` | string | present exactly when `instantiates` is false |
| `defaultRun` | object | one real call with a default key; absent when the type has no call |
| `transformations` | list | declared `algorithm/mode/padding` pairs: `name`, `instantiates`, `error`, `defaultRun` |

## defaultRun

| Field | Type | Description |
|---|---|---|
| `works` | bool | the call returned |
| `keyAlgorithm`, `keyProvider` | string | the key used |
| `keySize` | int | key size in bits, when known |
| `inputSize` | int | bytes passed |
| `providerChose` | string | what the provider filled in, e.g. `GCM iv=12B` |
| `bareName` | bool | the bare algorithm name was used, not a transformation |
| `error` | string | present exactly when `works` is false |
