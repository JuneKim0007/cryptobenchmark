# security_contract

Fields of a capture written by `ProviderProbe` → `EnvironmentYamlWriter`, one `probe_<utc timestamp>.yaml` per capture. Key names are the constants on `CaptureDocument`.

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

## discovery setting

Output of `DiscoverySettingConverter.convert(capture)` → `DiscoverySetting`. Kotlin objects; not
serialized (#21).

| Field | Type | Description |
|---|---|---|
| `schemaVersion` | int | setting format version |
| `capturedAtMillis` | long | time of the capture it was derived from |
| `device.model` | string | device model |
| `device.manufacturer` | string | device manufacturer |
| `device.hardware` | string | hardware name |
| `device.sdkInt` | int | Android API level |
| `device.release` | string | Android version |
| `providers[].name` | string | provider name |
| `providers[].version` | string | provider version |
| `providers[].precedence` | int | 1-based position in the search order |
| `providers[].usable` | bool | computed, not stored: at least one in-scope service remains |
| `providers[].services[].type` | string | service type |
| `providers[].services[].algorithm` | string | algorithm name |
| `providers[].services[].aliases` | list | alternate names |
| `providers[].services[].supportedModes` | list | declared modes; empty when undeclared |
| `providers[].services[].supportedPaddings` | list | declared paddings; empty when undeclared |
| `providers[].services[].keySize` | int | largest declared key size; null when undeclared |

In-scope service types: `Cipher`, `MessageDigest`, `Mac`, `Signature`, `KeyGenerator`,
`KeyPairGenerator`, `KeyAgreement` (`BenchmarkScope.TYPES`).

## cropped

Fields removed when converting a capture to the discovery setting.

| Field | Reason |
|---|---|
| `runtime.javaVersion` | not meaningful on the Android runtime |
| `providers[].info` | free-text description |
| `providers[].unresolvedAliases` | diagnostic about the capture, not used to select a service |
| `services[].className` | implementation detail |
| `services[]` with a type outside scope | not benchmarked |
| `attributes` other than `SupportedModes`, `SupportedPaddings`, `KeySize` | do not narrow the benchmark matrix |
