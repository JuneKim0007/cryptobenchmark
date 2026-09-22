# probe

Captures registered JCA providers and services, writes them as JSON, reduces them to a discovery setting.

Field contract: [security_contract.md](security_contract.md)

## Flow

```
Discovery(directory).probe(providers)         -> DiscoveryRun: capture, probe_<utc>.yaml, probe_classes_<utc>.yaml
Discovery(directory).trial(capture, providers) -> trial_<utc>.yaml

Security.getProviders() -> ProviderProbe -> CapturedEnvironment -> EnvironmentYamlWriter     -> probe_<utc>.yaml
                                                               -> DiscoverySettingConverter -> DiscoverySetting
                                                               -> TrialRunner -> TrialReport -> TrialYamlWriter -> trial_<utc>.yaml
```

## JCA APIs used

| API | Gives |
|---|---|
| `Security.getProviders()` (caller) | providers, in preference order |
| `Provider.getName()`, `getInfo()`, property `Provider.id version` | provider identity — Android has no `getVersionStr()` |
| `Provider.getServices()` | type, algorithm, class name |
| `Provider.stringPropertyNames()`, `getProperty()` | aliases, attributes |

## Property keys

| Raw property | `PropertyKey` | Captured as |
|---|---|---|
| `Provider.id name` | `ProviderMeta(field)` | kept in `PropertyMapIndex.meta`; `id version` becomes the entry's version |
| `Alg.Alias.Cipher.RC4` = `ARC4` | `Alias` | alias on target service |
| `Cipher.AES SupportedModes` = `ECB\|CBC` | `Attribute` | typed attribute |
| `Cipher.AES` | `ServiceImpl` | skipped; services come from `getServices()` |
| anything else | `Malformed` | dropped |

## Limits

- attributes are optional: `SupportedModes`, `SupportedPaddings`, `KeySize` often absent
- transformations resolved by fallback are not listed (`Cipher.AES` serves `AES/CBC/PKCS5Padding`)
- an alias is a name, not a separate implementation
- the trial instantiates (level 1), then calls once with a default key (level 2); a default run says nothing about other key sizes or parameters (#18)
- not visible: native crypto via JNI, providers not registered in this process, hardware (StrongBox, AES acceleration)

## Classes

Kotlin under `src/main/kotlin/`. `internal` means module-only, not part of the API.

| Class | Package | Role |
|---|---|---|
| `Discovery` | root | entry point; wires probe, trial and writers over one `ProbeDirectory`; `reusable(runtime)` returns the newest complete capture of that device, or null. `tools/jca-contract`: `./gradlew run --args=<dir>` |
| `DiscoveryRun` | root | what `probe` returns: the capture and the two files |
| `ProviderProbe` | `adapter` | JCA → capture; joins services with aliases and attributes |
| `PropertyMapIndex` | `adapter` | one provider's property map → aliases, attributes — `internal` |
| `PropertyKeyParser` | `adapter` | decodes the property-map grammar — `internal` |
| `PropertyKey` | `adapter` | one decoded key, discarded after use — sealed, `internal` |
| `DeclaredAlias` | `adapter` | one alias as declared — `internal` |
| `AttributeKind` | `adapter` | attribute name → `LIST`, `INT`, `BOOL`, `STRING` — `internal` |
| `AttributeValueParser` | `adapter` | attribute value → that type — `internal` |
| `DeviceRuntimeReader` | `adapter` | `android.os.Build` → `RuntimeInfo`, reflectively |
| `CapturedEnvironment` | `contract` | one capture |
| `ProviderEntry` | `contract` | one provider |
| `ServiceEntry` | `contract` | one service |
| `AliasEntry` | `contract` | one alias that resolved to nothing |
| `ServiceAttributes` | `contract` | typed attribute accessors |
| `RuntimeInfo` | `contract` | device and runtime provenance |
| `ServiceKey` | `contract` | `(type, algorithm)` key, `Locale.ROOT` folding — `internal` |
| `DiscoverySettingConverter` | `setting` | capture → setting |
| `BenchmarkScope` | `setting` | the 7 engine types measured |
| `DiscoverySetting` | `setting` | reduced setting; `providersFor`, `algorithms` |
| `ProviderSetting`, `ServiceSetting`, `Device` | `setting` | the reduced data |
| `ServiceLookup` | `setting` | find by name or alias — `internal` |
| `CaptureDocument` | `write` | the YAML schema: key names, capture → document (`of`), document → capture (`parse`) |
| `DocumentFields` | `write` | typed reads of one document key — `internal` |
| `EnvironmentYamlWriter` | `write` | document → `probe_<utc>.yaml` |
| `ProviderClassNameWriter` | `write` | provider → implementing class names, `probe_classes_<utc>.yaml` |
| `CaptureQuery` | `query` | `whoServes(type, name)` in precedence order, `serviceOf(provider, type, name)`, `namesOf`, `onlyOn(provider)`, `tree()` — pure, no JCA call |
| `TrialQuery` | `query` | `serviceTrial`, `transformationTrial`, `failingServices()`, `failingTransformations()`, `instantiationByProvider()` |
| `ServiceShape`, `TransformationFailure` | `query` | what `tree()` and `failingTransformations()` return |
| `ServiceIndex` | `query` | one provider's services by name or alias — `internal` |
| `ServiceTree` | `query` | builds `tree()`: merges spellings, unions modes and paddings — `internal` |
| `TrialRunner` | `trial` | capture × live providers → `TrialReport`: one outcome per service, one per declared cipher transformation |
| `Attempt` | `trial` | runs one instantiation, turns `Exception`/`LinkageError` into a `TrialOutcome` — `internal` |
| `DefaultRunTrial` | `trial` | level 2: one real call per instantiated service/transformation with a default key; records key algorithm, key provider, key size, input size used, what the provider chose, bare name |
| `DefaultCall`, `DefaultCalls` + one call per engine type | `trial/call` | registry of per-type calls; a type with no call gets no default run — `internal` |
| `DefaultKeys`, `KeyNames`, `KeyBits` | `trial/call` | default keys, cached per run; key algorithm from the name; key size in bits — `internal` |
| `DefaultRunOutcome` | `contract` | one default run; carries an error exactly when it fails |
| `TransformationSet` | `trial` | algorithm + algorithm/mode/padding for every declared pair — `internal` |
| `TrialReport`, `ServiceTrialEntry`, `TransformationTrialEntry`, `TrialOutcome` | `contract` | the trial model |
| `TrialDocument` | `write` | the trial YAML schema, `of` ⇄ `parse` |
| `TrialYamlWriter` | `write` | report → `trial_<utc>.yaml` |
| `YamlCodec` | `write` | document ⇄ YAML text, a `Yaml` per call |
| `ProbeDirectory` | `write` | output directory, injected into the writers; `create` fails on an existing name |
| `ProbeFileName` | `write` | `<prefix>_<utc>.yaml` — `internal` |

## Drift alarm

`src/test/kotlin/JcaContractTest.kt` asserts the limits above against the running JVM. The
`jca contract` workflow runs it weekly on Java 17, 21 and 25 and attaches each capture. A
failure means the JCA moved. Android providers are not covered (#14).

## Not yet

| Missing | Issue |
|---|---|
| read a capture back | #21 |
| verify key sizes by trial | #18 |
| run as an independent process | #16 |
