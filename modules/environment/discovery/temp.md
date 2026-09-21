# temp — field ↔ contract map (reading aid, not part of the module docs)

Sources under `src/main/kotlin/`: `adapter/`, `contract/`, `setting/`, `write/`. Line numbers are `File.kt:line`.

## Responsibilities, one per file

| Package | File | Owns |
|---|---|---|
| `adapter` | `ProviderProbe` | providers in, capture out; joins services with their aliases and attributes |
| `adapter` | `PropertyMapIndex` | walks one provider's property map into aliases and attributes |
| `adapter` | `PropertyKeyParser` | which of the four shapes a raw key is |
| `adapter` | `PropertyKey` | the parse result |
| `adapter` | `DeclaredAlias` | one alias as declared, before resolution |
| `adapter` | `AttributeKind` | which type an attribute name has |
| `adapter` | `AttributeValueParser` | turning an attribute value into that type |
| `adapter` | `DeviceRuntimeReader` | reads `android.os.Build` reflectively |
| `contract` | `CapturedEnvironment`, `ProviderEntry`, `ServiceEntry`, `AliasEntry`, `RuntimeInfo`, `ServiceAttributes` | data, validated at construction |
| `contract` | `ServiceKey`, `ServiceKeyException` | when two service names are the same |
| `setting` | `DiscoverySettingConverter` | crop a capture to the benchmark scope |
| `setting` | `BenchmarkScope` | the 7 engine types we measure |
| `setting` | `DiscoverySetting`, `ProviderSetting`, `ServiceSetting`, `Device` | the reduced data |
| `setting` | `ServiceLookup` | find a service by name or alias |
| `write` | `CaptureDocument` | the YAML key names, and capture → document |
| `write` | `EnvironmentYamlWriter` | document → `probe_<utc>.yaml` |
| `write` | `ProviderClassNameWriter` | capture → class list document |
| `write` | `YamlDocument` | document → YAML text |
| `write` | `ProbeFile` | timestamped name, directory, write |

## Legend

Kotlin states optionality in the type, so there is no separate column:

| Declaration | Meaning |
|---|---|
| `val x: String` | required — no call site can pass null, checked by the compiler |
| `val x: String = ""` | defaulted — omit it and you get `""` |
| `val x: Int?` | nullable — the only fields that can be absent at runtime |
| `val x get() = …` | computed, not stored; cannot disagree with the fields it reads |

| YAML column | Meaning |
|---|---|
| always | key always written (value may be `''` or `0`) |
| omitted when empty | key absent when the list is empty |

## Flow

```
Provider[]                                   (caller: Security.getProviders())
  └─ ProviderProbe.capture            :14
       ├─ PropertyMapIndex.of      :16   property map → aliases, attributes
       └─ toEntry                  :24   getServices() + index → ProviderEntry
  → CapturedEnvironment ──► EnvironmentYamlWriter.write :35    ──► probe_<utc>.yaml
                        ──► ProviderClassNameWriter.write :29  ──► probe_classes_<utc>.yaml
                        └─► DiscoverySettingConverter.convert :17 ──► DiscoverySetting (Kotlin only, never written)
```

## 1. Raw property key → `PropertyKey`

`PropertyKeyParser.classify` :18. A sealed class: each kind carries only the parts it guarantees.

| Raw key (value) | Subclass :line | Carries | Probe does |
|---|---|---|---|
| `Provider.id name` | `ProviderMeta` :10 | nothing | ignore |
| `Alg.Alias.Cipher.RC4` (`ARC4`) | `Alias` :13 | `type`, `name` = the **alias** | `Alias(type, name, value)` — value is the target |
| `Cipher.AES SupportedModes` (`ECB\|CBC`) | `Attribute` :15 | `type`, `algorithm`, `name` = the **attribute** | `attributes[ServiceKey][name] = parse(value)` |
| `Cipher.AES` | `ServiceImpl` :17 | `type`, `algorithm` | ignore (services come from `getServices()`) |
| no dot / empty part | `Malformed` :11 | nothing | ignore |

`when` over these is exhaustive — adding a kind breaks the build until the probe handles it.

## 2. Capture: Kotlin → YAML

Null and ordering are normalised in `ProviderProbe`, at the JCA boundary. The model classes are plain data.

### `CapturedEnvironment` → root

| Field | Declaration | YAML key | YAML | Filled from |
|---|---|---|---|---|
| `runtime` | `RuntimeInfo` required | `runtime` | always | argument, default `RuntimeInfo.unknown()` |
| `providers` | `List<ProviderEntry>` = empty | `providers` | always (may be `[]`) | one `toEntry` per provider, array order |
| `capturedAtMillis` | `Long` = now | `capturedAtMillis` | always | argument; also names the file |
| `schemaVersion` | `Int` = `SCHEMA_VERSION` (1) | `schemaVersion` | always | constant |

### `RuntimeInfo` → `runtime`

| Field | Declaration | YAML | `DeviceRuntimeReader.read()` source |
|---|---|---|---|
| `model` | `String` = `""` | always | `Build.MODEL` |
| `manufacturer` | `String` = `""` | always | `Build.MANUFACTURER` |
| `hardware` | `String` = `""` | always | `Build.HARDWARE` |
| `sdkInt` | `Int` = `0` | always | `Build.VERSION.SDK_INT` |
| `release` | `String` = `""` | always | `Build.VERSION.RELEASE` |
| `javaVersion` | `String` = system property | always | `java.version` |

`DeviceRuntimeReader` reads `Build` reflectively; any failure → `""` / `0`. `RuntimeInfo.unknown()` is every default.

### `ProviderEntry` → `providers[]`

| Field | Declaration | YAML key | YAML | Filled from |
|---|---|---|---|---|
| `name` | `String` required | `name` | always | `provider.name` |
| `precedence` | `Int` required, `require(>= 1)` | `precedence` | always | loop index + 1 |
| `version` | `String` = `""` | `version` | always | `provider.versionStr` |
| `info` | `String` = `""` | `info` | always | `provider.info ?: ""` |
| `services` | `List<ServiceEntry>` = empty | `services` | always (may be `[]`) | sorted by type, then algorithm, in the probe |
| `unresolvedAliases` | `List<AliasEntry>` = empty | `unresolvedAliases` | **omitted when empty** | aliases whose target is not registered |
| `usable` | **computed** `services.isNotEmpty()` | `usable` | always | — |

### `AliasEntry` → `unresolvedAliases[]`

| Field | Declaration | YAML key |
|---|---|---|
| `type` | `String` required, non-blank | `type` |
| `name` | `String` required, non-blank | `alias` |
| `target` | `String` required, non-blank | `target` |

Resolved aliases are not here — they sit on the service they resolve to.

### `ServiceEntry` → `services[]`

| Field | Declaration | YAML key | YAML | Filled from |
|---|---|---|---|---|
| `type` | `String` required | `type` | always | `service.type`, original case |
| `algorithm` | `String` required | `algorithm` | always | `service.algorithm`, original case |
| `className` | `String` = `""` | `className` | always | `service.className ?: ""` |
| `aliases` | `List<String>` = empty | `aliases` | **omitted when empty** | aliases targeting this service, sorted in the probe |
| `attributes` | `ServiceAttributes` = empty | `attributes` | **omitted when empty** | attributes indexed by `ServiceKey` |

### `ServiceAttributes` → `attributes`

Every attribute is optional. Values are parsed on the way in (`AttributeValueParser.parseOrRaw`) and held in a sorted map.

| Attribute | `AttributeKind` | Stored as | Accessor :line | When absent |
|---|---|---|---|---|
| `SupportedModes` | `LIST` | `List<String>` (split on `\|`) | `supportedModes` :11 | empty list |
| `SupportedPaddings` | `LIST` | `List<String>` | `supportedPaddings` :13 | empty list |
| `KeySize` | `INT` | `Int`, or raw `String` if not a number | `keySize` :9 | **null** (also null when raw `String`) |
| anything else | per `AttributeKind`, default `STRING` | as parsed | `integer` :15, `strings` :18 | written to YAML, no typed accessor |

## 3. Class list: `ProviderClassNameWriter` :19

`<provider name>` → distinct, sorted `className` of every service. One file, `probe_classes_<utc>.yaml`.

## 4. Capture → `DiscoverySetting`

`DiscoverySettingConverter.convert` :17. Never written to a file.

| Setting field | Declaration | ← Capture | Rule |
|---|---|---|---|
| `device` | `Device` required | `capture.runtime` | 5 of 6 fields; `javaVersion` dropped |
| `providers` | `List<ProviderSetting>` = empty | `capture.providers` | **all kept**, sorted by precedence |
| `capturedAtMillis` | `Long` = `0L` | same | copied |
| `schemaVersion` | `Int` = `SCHEMA_VERSION` (1) | — | the setting's own version |
| `ProviderSetting.name` / `precedence` / `version` | as `ProviderEntry` | copied | `info`, `unresolvedAliases` dropped |
| `ProviderSetting.services` | `List<ServiceSetting>` = empty | `ProviderEntry.services` | only types in `BenchmarkScope.TYPES` |
| `ProviderSetting.usable` | **computed** | — | in-scope services non-empty |
| `ProviderSetting.find` | delegates to `ServiceLookup` | — | `ServiceKey(type, algorithm)` and `ServiceKey(type, alias)` → service |
| `ServiceSetting.type` / `algorithm` / `aliases` | as `ServiceEntry` | copied | `className` dropped |
| `ServiceSetting.supportedModes` / `supportedPaddings` | `List<String>` = empty | attributes | empty = undeclared |
| `ServiceSetting.keySize` | **`Int?`** | `attributes.keySize` | null = undeclared or unparseable |

Lookups that can find nothing:

| Call | Nothing found |
|---|---|
| `ProviderSetting.find(type, nameOrAlias)` :62 | **null** |
| `DiscoverySetting.providersFor(type, nameOrAlias)` :19 | empty list |
| `DiscoverySetting.algorithms(type)` :23 | empty set |

## 5. Matching rules

| Where | Rule |
|---|---|
| `ServiceKey(type, algorithm)` :7 | both folded with `Locale.ROOT` in the constructor; blank → `ServiceKeyException` |
| stored names (`ServiceEntry`, YAML) | original case, never folded |
| alias → service | same provider, same type, folded algorithm name |
| `providersFor` :19 | providers whose index has the key, in precedence order |
| `algorithms` :23 | canonical `algorithm` names only, not aliases |

## 6. Visibility

| `internal` (module-only) | `public` (the module's API) |
|---|---|
| `PropertyKey`, `PropertyKeyParser`, `PropertyMapIndex`, `DeclaredAlias`, `AttributeKind`, `AttributeValueParser`, `ServiceKey`, `ServiceKeyException`, `ServiceLookup`, `YamlDocument`, `ProbeFile`, `ServiceAttributes.document()` | `ProviderProbe`, `DeviceRuntimeReader`, `CapturedEnvironment`, `ProviderEntry`, `ServiceEntry`, `AliasEntry`, `ServiceAttributes`, `RuntimeInfo`, `EnvironmentYamlWriter`, `ProviderClassNameWriter`, `DiscoverySettingConverter`, `BenchmarkScope`, `DiscoverySetting`, `ProviderSetting`, `ServiceSetting`, `Device` |
