# temp — field ↔ contract map (reading aid, not part of the module docs)

Sources live under `src/main/kotlin/`: `probe/`, `capture/`, `setting/`, plus `ServiceKey.kt`
and `EnvironmentJsonWriter.kt` at the root. Line numbers below are `File.kt:line`.

## Legend

Kotlin states optionality in the type, so there is no separate column:

| Declaration | Meaning |
|---|---|
| `val x: String` | required — no call site can pass null, checked by the compiler |
| `val x: String = ""` | defaulted — omit it and you get `""` |
| `val x: Int?` | nullable — the only fields that can be absent at runtime |
| `val x get() = …` | computed, not stored; cannot disagree with the fields it reads |

| JSON column | Meaning |
|---|---|
| always | key always written (value may be `""` or `0`) |
| omitted when empty | key absent when the list/map is empty |

## Flow

```
Provider[]                                   (caller: Security.getProviders())
  └─ ProviderProbe.capture         :16
       ├─ index       :59   property map → aliases, attributes
       └─ toEntry     :26   getServices() + aliases + attributes → ProviderEntry
  → CapturedEnvironment ──► EnvironmentJsonWriter.toJson :10 ──► capture JSON
                        └─► DiscoverySettingConverter.convert :13 ──► DiscoverySetting (Kotlin only, no JSON yet)
```

## 1. Raw property key → `PropertyKey`

`PropertyKey.classify` :31. A sealed class: each kind carries only the parts it guarantees, so
there is no field that is meaningful for one kind and null for another.

| Raw key (value) | Subclass :line | Carries | Probe does |
|---|---|---|---|
| `Provider.id name` | `ProviderMeta` :10 | nothing | ignore |
| `Alg.Alias.Cipher.RC4` (`ARC4`) | `Alias` :16 | `type`, `name` = the **alias** | `Alias(type, name, value)` — value is the target |
| `Cipher.AES SupportedModes` (`ECB\|CBC`) | `Attribute` :19 | `type`, `algorithm`, `name` = the **attribute** | `attributes[serviceKey][name] = parse(value)` |
| `Cipher.AES` | `ServiceImpl` :24 | `type`, `algorithm` | ignore (services come from `getServices()`) |
| no dot / empty part | `Malformed` :13 | nothing | ignore |

`when` over these is exhaustive — adding a kind breaks the build until the probe handles it.

## 2. Capture: Kotlin → JSON

Null and ordering are normalised in `ProviderProbe`, at the JCA boundary. The model classes are
plain data and do no defaulting of their own.

### `CapturedEnvironment` → root

| Field | Declaration | JSON key | JSON | Filled from |
|---|---|---|---|---|
| `runtime` | `RuntimeInfo` required | `runtime` | always | argument, default `RuntimeInfo.unknown()` |
| `providers` | `List<ProviderEntry>` = empty | `providers[]` | always (may be `[]`) | one `toEntry` per provider, array order |
| `capturedAtMillis` | `Long` = now | `capturedAtMillis` | always | argument |
| `schemaVersion` | `Int` = `SCHEMA_VERSION` (1) | `schemaVersion` | always | constant |

### `RuntimeInfo` → `runtime`

| Field | Declaration | JSON | `ofDevice()` source |
|---|---|---|---|
| `model` | `String` = `""` | always | `Build.MODEL` |
| `manufacturer` | `String` = `""` | always | `Build.MANUFACTURER` |
| `hardware` | `String` = `""` | always | `Build.HARDWARE` |
| `sdkInt` | `Int` = `0` | always | `Build.VERSION.SDK_INT` |
| `release` | `String` = `""` | always | `Build.VERSION.RELEASE` |
| `javaVersion` | `String` = system property | always | `java.version` |

`Build` is read reflectively; any failure → `""` / `0`, so those values mean "unknown".
`unknown()` is `RuntimeInfo()` — every default.

### `ProviderEntry` → `providers[]`

| Field | Declaration | JSON key | JSON | Filled from |
|---|---|---|---|---|
| `name` | `String` required | `name` | always | `provider.name` |
| `precedence` | `Int` required, `require(>= 1)` | `precedence` | always | loop index + 1 |
| `version` | `String` = `""` | `version` | always | `provider.version.toString()` → `"1.0"` |
| `info` | `String` = `""` | `info` | always | `provider.info ?: ""` |
| `services` | `List<ServiceEntry>` = empty | `services[]` | always (may be `[]`) | sorted by type, then algorithm, in the probe |
| `unresolvedAliases` | `Map<String, String>` = empty | `unresolvedAliases` | **omitted when empty** | aliases whose target is not registered; key `"<type> <alias>"` |
| `usable` | **computed** `services.isNotEmpty()` | `usable` | always | — |

### `ServiceEntry` → `services[]`

| Field | Declaration | JSON key | JSON | Filled from |
|---|---|---|---|---|
| `type` | `String` required | `type` | always | `service.type`, original case |
| `algorithm` | `String` required | `algorithm` | always | `service.algorithm`, original case |
| `className` | `String` = `""` | `className` | always | `service.className ?: ""` |
| `aliases` | `List<String>` = empty | `aliases` | **omitted when empty** | aliases targeting this service, sorted in the probe |
| `attributes` | `ServiceAttributes` = empty | `attributes` | **omitted when empty** | attributes indexed by `ServiceKey` |
| `key` | **computed** `ServiceKey.of(type, algorithm)` | — | — | `internal` |

### `ServiceAttributes` → `attributes`

Every attribute is optional: present only if the provider declares it. Values are parsed on the way
in (`parseOrRaw` :80) and held in a sorted map, which is what makes the JSON byte-stable.

| Attribute | `AttributeKind` | Stored as | Accessor :line | When absent |
|---|---|---|---|---|
| `SupportedModes` | `LIST` | `List<String>` (split on `\|`) | `supportedModes` :13 | empty list |
| `SupportedPaddings` | `LIST` | `List<String>` | `supportedPaddings` :15 | empty list |
| `SupportedKeyClasses` | `LIST` | `List<String>` | `supportedKeyClasses` :17 | empty list |
| `SupportedKeyFormats` | `LIST` | `List<String>` | `supportedKeyFormats` :19 | empty list |
| `SupportedCurves` | `LIST` | `List<String>` | `supportedCurves` :21 | empty list |
| `KeySize` | `INT` | `Int`, or raw `String` if not a number | `keySize` :11 | **null** (also null when raw `String`) |
| `ThreadSafe` | `BOOL` | `Boolean` | `threadSafe` :23 | `false` |
| `ImplementedIn`, `MechanismType` | `STRING` | `String` | `text(name)` :26 | **null** |
| anything else | `STRING` | `String` | `text(name)` :26 | **null** |

Absent and declared-empty are indistinguishable through the list accessors.

## 3. Capture → `DiscoverySetting`

`DiscoverySettingConverter.convert` :13. No JSON writer exists for the setting.

| Setting field | Declaration | ← Capture | Rule |
|---|---|---|---|
| `device` | `Device` required | `capture.runtime` | 5 of 6 fields; `javaVersion` dropped |
| `providers` | `List<ProviderSetting>` = empty | `capture.providers` | **all kept**, sorted by precedence |
| `capturedAtMillis` | `Long` = `0L` | same | copied |
| `schemaVersion` | `Int` = `SCHEMA_VERSION` (1) | — | the setting's own version |
| `ProviderSetting.name` | `String` required | `ProviderEntry.name` | copied |
| `ProviderSetting.precedence` | `Int` required | `ProviderEntry.precedence` | copied |
| `ProviderSetting.version` | `String` = `""` | `ProviderEntry.version` | copied; `info`, `unresolvedAliases` dropped |
| `ProviderSetting.services` | `List<ServiceSetting>` = empty | `ProviderEntry.services` | only types in `BENCHMARKED_TYPES` :48 |
| `ProviderSetting.usable` | **computed** | — | in-scope services non-empty |
| `ProviderSetting.byNameOrAlias` | private, built in the initialiser :39 | — | `ServiceKey(type, algorithm)` and `ServiceKey(type, alias)` → service |
| `ServiceSetting.type` / `algorithm` | `String` required | `ServiceEntry` same | copied; `className` dropped |
| `ServiceSetting.aliases` | `List<String>` = empty | `ServiceEntry.aliases` | copied |
| `ServiceSetting.supportedModes` | `List<String>` = empty | `attributes.supportedModes` | empty = undeclared |
| `ServiceSetting.supportedPaddings` | `List<String>` = empty | `attributes.supportedPaddings` | empty = undeclared |
| `ServiceSetting.keySize` | **`Int?`** | `attributes.keySize` | null = undeclared or unparseable |

Lookups that can find nothing:

| Call | Nothing found |
|---|---|
| `ProviderSetting.find(type, nameOrAlias)` :60 | **null** |
| `DiscoverySetting.providersFor(type, nameOrAlias)` :17 | empty list |
| `DiscoverySetting.algorithms(type)` :21 | empty set |

## 4. Matching rules

| Where | Rule |
|---|---|
| `ServiceKey.of` :12 | type and algorithm uppercased with `Locale.ROOT`; used for every lookup |
| stored names (`ServiceEntry`, JSON) | original case, never folded |
| alias → service | same provider, same type, folded algorithm name |
| `providersFor` :17 | providers whose index has the key, in precedence order |
| `algorithms` :21 | canonical `algorithm` names only, not aliases |

## 5. Visibility

| `internal` (module-only) | `public` (the module's API) |
|---|---|
| `PropertyKey`, `AttributeKind`, `ServiceKey`, `ServiceEntry.key`, `ServiceAttributes.document()` | `ProviderProbe`, `CapturedEnvironment`, `ProviderEntry`, `ServiceEntry`, `ServiceAttributes`, `RuntimeInfo`, `EnvironmentJsonWriter`, `DiscoverySettingConverter`, `DiscoverySetting` |

## 6. Mismatches between code and `security_contract.md`

| Contract says | Code does |
|---|---|
| setting has field `providers[].usable` | computed property, not a stored field |
| setting is described with JSON-style paths | the setting is never serialized |
| capture attribute `KeySize` is `int` | can be a raw `String` when unparseable |
| no optionality column | the Kotlin types carry it; see the tables above |
