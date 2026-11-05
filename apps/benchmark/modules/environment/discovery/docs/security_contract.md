# security_contract

Fields of the files discovery writes. Key names live on `CaptureDocument` and `TrialDocument`. Config and preparation read these files by key name; no discovery class is on their classpath.

| rule | value |
|---|---|
| version check | each `parse` rejects another `schemaVersion`: `unsupported_schema_version: <v>, this build reads <n>` |
| read failures | `missing_field: <key>`, `wrong_type: <key>` |
| pairing | a trial belongs to the capture with the same `capturedAtMillis`; config refuses a mismatch with `mismatched_trial: capture <a>, trial <b>` |

## capture

Top-level keys, in this order.

| field | type | description |
|---|---|---|
| `schemaVersion` | int | `1` |
| `capturedAtMillis` | long | capture time, epoch milliseconds: the host's on a device run, since a device clock can be months off |
| `deviceClockMillis` | long | the running device's or JVM's own clock at capture |
| `runtime` | object | device the capture was taken on |
| `providers` | list | installed providers, in precedence order |

## runtime

| field | type | description |
|---|---|---|
| `model` | string | device model |
| `manufacturer` | string | device manufacturer |
| `hardware` | string | hardware name |
| `sdkInt` | int | Android API level; `0` on a JVM |
| `release` | string | Android version |
| `javaVersion` | string | `java.version` |
| `defaultKeySizeProperty` | string | system property `jdk.security.defaultKeySize`; `''` when unset |
| `fingerprint` | string | `Build.FINGERPRINT`; `''` on a JVM |
| `javaVendor` | string | `java.vendor` |
| `javaRuntimeVersion` | string | `java.runtime.version` |
| `osName` | string | `os.name` |
| `osArch` | string | `os.arch` |

Every runtime field is required on read.

## providers[]

| field | type | description |
|---|---|---|
| `name` | string | provider name |
| `version` | string | property `Provider.id version` |
| `precedence` | int | 1-based position in the search order |
| `origin` | string | `platform`, or `bundled` for a provider the app ships and `BundledInstaller` installed; required on read |
| `services` | list | services the provider registers |
| `artifact` | string | `group:name:version` of a bundled provider; omitted for `platform` |

## services[]

| field | type | description |
|---|---|---|
| `type` | string | service type, e.g. `Cipher` |
| `algorithm` | string | algorithm name |
| `className` | string | implementing class |
| `aliases` | list | alternate names; omitted when empty |
| `attributes` | map | declared attributes, sorted keys; omitted when empty |

## attributes

| field | type | description |
|---|---|---|
| `SupportedModes` | list | cipher modes |
| `SupportedPaddings` | list | cipher paddings |
| `SupportedKeyClasses` | list | accepted key classes |
| `SupportedKeyFormats` | list | accepted encoded key formats |
| `SupportedCurves` | list | supported elliptic curves |
| `KeySize` | int | raw string when it does not parse |
| `ThreadSafe` | bool | any value other than `true` reads as false |
| `ImplementedIn` | string | as declared |
| `MechanismType` | string | as declared |
| any other | string | vendor attribute, raw |

## trial

| field | type | description |
|---|---|---|
| `schemaVersion` | int | `3` |
| `capturedAtMillis` | long | the capture this trial belongs to |
| `defaultRunInputSize` | int | the input size every default run tries first; written only when set |
| `services` | list | one entry per captured service |

## services[] (trial)

| field | type | description |
|---|---|---|
| `provider`, `type`, `algorithm` | string | the service |
| `instantiates` | bool | instantiation succeeded |
| `error` | string | present exactly when `instantiates` is false |
| `defaultRun` | object | absent when the type has no call, the provider is not installed, or instantiation failed |
| `transformations` | list | Cipher only; omitted when empty; each declared `alg/mode/padding` |

## transformations[]

| field | type | description |
|---|---|---|
| `name` | string | transformation name |
| `instantiates` | bool | `Cipher.getInstance(name, provider)` succeeded |
| `error` | string | present exactly when `instantiates` is false |
| `defaultRun` | object | absent when instantiation failed |

## defaultRun

`works` first; each other field only when set.

| field | type | description |
|---|---|---|
| `works` | bool | the call returned |
| `keyAlgorithm`, `keyProvider` | string | the key used |
| `keySize` | int | key size in bits, `> 0` |
| `fixedKeySize` | int | the size the service name fixes, e.g. a `<base>_<n>` name; preparation asks for it; absent otherwise |
| `inputSize` | int | bytes passed, `>= 0`; absent for KeyAgreement and generators |
| `providerChose` | string | what the provider filled in, e.g. `ivBytes=12 tagBits=128`; format in [probe.md](probe.md) |
| `bareName` | bool | `true` when the name has no `/` |
| `keyMaterial` | string | a generator's key, or a pair's private key: `exportable` (`getEncoded()` returned bytes) or `non_exportable` (null); absent for other types and a generator that did not run |
| `keyFormat` | string | the same key's `getFormat()`, e.g. `RAW`, `PKCS#8`; absent when null, for other types and a generator that did not run |
| `triedKeys` | list | a generator whose default ran: each other size asked of it, `size` with that key's `keyMaterial` and `keyFormat`, or `refused: true`; secret keys 128, 192, 256; a pair 256, 384, 1024, 2048 below its default, none without a default size |
| `error` | string | present exactly when `works` is false |
