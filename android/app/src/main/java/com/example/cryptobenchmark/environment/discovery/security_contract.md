# security_contract

Fields of a capture written by `ProviderProbe` → `EnvironmentJsonWriter`.

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

## providers[]

| Field | Type | Description |
|---|---|---|
| `name` | string | provider name |
| `version` | string | provider version |
| `precedence` | int | 1-based position in the search order |
| `info` | string | provider description |
| `usable` | bool | false when the provider registers no services |
| `services` | list | services the provider registers |
| `unresolvedAliases` | map | aliases whose target service is not registered; omitted when empty |

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
| `KeySize` | int | largest supported key size |
| `ThreadSafe` | bool | implementation is thread safe |
| `ImplementedIn` | string | `Software` or `Hardware` |
| `MechanismType` | string | mechanism type |
| *any other* | string | vendor attribute, kept raw |

## cropped

Fields removed when converting a capture to the discovery setting.

| Field | Reason |
|---|---|
| — | not decided yet |
