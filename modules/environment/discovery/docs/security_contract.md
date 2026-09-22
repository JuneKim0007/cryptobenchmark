# security_contract

Fields of a capture written by `ProviderProbe` → `EnvironmentYamlWriter`, one `probe_<utc timestamp>.yaml` per capture. Key names are the constants on `CaptureDocument`; `CaptureDocument.parse` reads a document back and rejects any other `schemaVersion`.

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

