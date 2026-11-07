# probe

Captures registered JCA providers and services, writes them as YAML, calls each service once, then measures what each requires.

File fields: [security_contract.md](security_contract.md). File map: [index.md](index.md).

## Flow

```
Discovery(directory).probe(providers)          -> DiscoveryRun: capture, probe_<utc>.yaml
Discovery(directory).trial(capture, providers) -> TrialFiles: trial_<utc>.yaml, requirements_<utc>.yaml
Discovery(directory).reusable(runtime)         -> ReusedRun or null

Provider[] -> ProviderProbe -> CapturedEnvironment -> EnvironmentYamlWriter
CapturedEnvironment -> TrialRunner -> DefaultRunTrial -> TrialReport -> TrialYamlWriter
CapturedEnvironment, TrialReport -> RequirementTrial -> RequirementReport -> RequirementYamlWriter
```

| entry | caller |
|---|---|
| host | `ProbeKt` in `apps/benchmark/cli`, passes `Security.getProviders()`; command line in `docs/tools.md` |
| device | `DeviceProbe` in `apps/benchmark/modules/android`: `BundledInstaller.install`, then `probe` with what it installed, then `trial` |
| runtime default | `probe` and `reusable` default to `DeviceRuntimeReader.read()` |

## JCA APIs used

| API | gives |
|---|---|
| `Security.getProviders()` (caller) | providers; precedence = 1-based array index, `>= 1` enforced |
| `Provider.getName()`, property `Provider.id version` | provider identity |
| `Provider.getServices()` | type, algorithm, class name (`""` when null); sorted by (type, algorithm) |
| `Provider.stringPropertyNames()`, `getProperty()` | aliases, attributes; blank values skipped |

## Property keys

| raw property | `PropertyKey` | captured as |
|---|---|---|
| `Provider.<field>` | `ProviderMeta` | meta; `id version` is the provider version |
| `Alg.Alias.<type>.<name>` | `Alias` | alias on the service whose case-folded (type, target) matches; else dropped |
| `<type>.<alg> <attr>` | `Attribute` | typed attribute |
| `<type>.<alg>` | `ServiceImpl` | ignored; services come from `getServices()` |
| anything else | `Malformed` | dropped |

| attribute kind | names | parse |
|---|---|---|
| LIST | `SupportedModes`, `SupportedPaddings`, `SupportedKeyClasses`, `SupportedKeyFormats`, `SupportedCurves` | split on `\|`, trim, drop empties |
| INT | `KeySize` | raw string kept when unparsable |
| BOOL | `ThreadSafe` | `toBoolean()` |
| STRING | `ImplementedIn`, `MechanismType`, any other | as written |

`ServiceKey` folds type and algorithm with `uppercase(Locale.ROOT)`; a blank part fails `missing_field`.

## Bundled providers

| step | class | does |
|---|---|---|
| read | `BundledProviders.read(document)` | the `bundledProviders` list of `{artifact, create, alias?}` from any map: the instrumentation argument or `effective.yaml` |
| create | `ProviderFactory(classLoader)` | `create` is `Class` (public no-argument constructor) or `Class#staticFactory` (public static, no arguments); failures `bundled_class_not_found`, `bundled_factory_not_found`, `bundled_factory_not_static`, `bundled_create_failed`, `bundled_not_a_provider` |
| register | `BundledInstaller.install(list)` | `Security.addProvider`, which always appends, never inserts; a name already installed needs `alias`, else `bundled_name_taken`; a taken alias fails `bundled_alias_taken` |
| alias | `AliasedProvider(alias, provider)` | forwards `getService` and `getServices`; each service is re-bound so an instance reports the alias; property map copied except `Provider.id*` |
| record | `ProviderProbe.capture(..., bundled)` | an installed name gets `origin: bundled` and its `artifact`; every other provider `platform` |

Errors are `BundledProviderException` with a `code`. The preparation and perf-repair readers ignore capture keys they do not know; discovery's own reader requires `origin`, so `reusable` re-probes over a capture without it.

## Runtime

`DeviceRuntimeReader.read()` reads `android.os.Build` `MODEL`, `MANUFACTURER`, `HARDWARE`, `FINGERPRINT` and `Build$VERSION` `RELEASE`, `SDK_INT` reflectively (`""` and `0` on a JVM), `java.version`, `java.vendor`, `java.runtime.version`, `os.name`, `os.arch`, and `jdk.security.defaultKeySize`. A capture without the identity fields does not parse, so `reusable` re-probes.

## Trial

| level | class | does |
|---|---|---|
| 1 | `TrialRunner` | each captured service: `provider.getService(type, alg).newInstance(null)`; provider absent from the live list: `provider_not_installed` |
| 1 | `TrialRunner` | Cipher services also try every declared `TransformationSet` name with `Cipher.getInstance(name, provider)`; a provider declaring no modes and paddings has none |
| 2 | `DefaultRunTrial` | one real call per instantiated service and transformation with a default key |
| 3 | `RequirementTrial` | per registered service and declared transformation, one guarded call per fact ([requirements.md](requirements.md)) |

| rule | value |
|---|---|
| `TransformationSet` | `alg/mode/padding` for each `SupportedModes` x `SupportedPaddings` |
| `Attempt` | every level's one catch: `Exception` and `LinkageError` are the attempt's result, any other `Error` (`OutOfMemoryError`) ends the probe; error text `<SimpleName>: <message>` through `ErrorText`, as at every level ([requirements.md](requirements.md)) |
| types with a default call | Cipher, Signature, Mac, MessageDigest, KeyGenerator, KeyPairGenerator, KeyAgreement (case-folded) |
| no default run | type has no call, provider not installed, or the service or transformation failed to instantiate |
| input-taking calls | Cipher, Signature, Mac, MessageDigest; KeyAgreement and generators take none (`inputSize` absent) |
| input sizes | tried in order; first working size returns, else the first failure is recorded |
| trial file stamp | the capture's `capturedAtMillis` |

| call | default run |
|---|---|
| Cipher | `ENCRYPT_MODE`, `doFinal(input)`; key from the first `KeyGenerator` candidate (base name, `<base>_<n>` size suffix, part before `-`), else a key pair's public key |
| Cipher `providerChose` | space-separated `key=value`, keys as prepared.yaml `resolvedParameters`, read back through `ParameterReadBack.describe` (contract/, shared by levels 2 and 3): `ivBytes=<n> tagBits=<n>` for GCM; `digest=<d> mgf1=<d> labelBytes=<n>` for OAEP; else `ivBytes=<n>` when a second init fills in a different value, `fixedValueBytes=<n>` when it fills in the same one (a key-wrap integrity check value); `""` without parameters; `bareName` when the name has no `/` |
| Signature | key algorithm = text after the last `with`, minus `inP1363Format`, `ECDSA` to `EC` |
| KeyAgreement | `ECDH` to `EC`; peer pair generated with the same EC or DH parameters |
| KeyGenerator, KeyPairGenerator | provider default size: key size, whether the key (a pair's private key) encodes, its format; then the other sizes in `triedKeys` ([security_contract.md](security_contract.md)) |

| default key rule | value |
|---|---|
| cache | per run, by (preferred provider, folded algorithm, size) |
| generator order | preferred provider first, then the others; none: `no provider generates <alg>` |
| key size bits | RSA modulus, EC field size, DSA/DH `p`, secret key encoded length x 8, else null |

## Output files and reuse

| rule | value |
|---|---|
| names | `probe_<utc>.yaml`, `trial_<utc>.yaml`, `requirements_<utc>.yaml` |
| stamp | `yyyyMMdd'T'HHmmss'Z'`, UTC, from `capturedAtMillis`: on a device the host's time, passed as the instrumentation argument `hostMillis` |
| create | `ProbeDirectory.create` makes the directory and writes `CREATE_NEW` |
| existing name | `FileAlreadyExistsException`: `probe_exists: a capture is never overwritten; probe again after a second, or remove the file` |
| newest | greatest file name matching `<prefix>_\d{8}T\d{6}Z.yaml` |
| YAML | block style, indent 2, a new `Yaml` per call |

`reusable(runtime)` returns null unless every check holds:

| check |
|---|
| newest `probe_<stamp>.yaml` parses |
| its `runtime` equals the given runtime |
| sibling `trial_` and `requirements_` files exist |
| both parse and their `capturedAtMillis` equals the capture's |

## Limits

- only what a provider registers and declares is captured; JNI crypto, unregistered providers and hardware are not visible
- attributes are optional: `SupportedModes`, `SupportedPaddings`, `KeySize` are often absent
- transformations resolved by fallback are not declared (`Cipher.AES` serves `AES/CBC/PKCS5Padding`)
- an alias is a name, not a separate implementation
- a default run covers one key and the provider's default parameters

## Tunables

| value | where | default |
|---|---|---|
| input sizes a default run tries, in order | `DefaultRunTrial(inputSizes)` | `[1024, 32]`; non-empty, all `>= 0`; the first is written as `defaultRunInputSize` |

## Drift alarm

| test | asserts |
|---|---|
| `JcaContractTest` | precedence `1..n`; Cipher AES, MessageDigest SHA-256, Mac HmacSHA256, Signature SHA256withRSA, KeyPairGenerator RSA resolve; SunJCE AES instantiates; `AES/CBC/PKCS5Padding` tried; some declared transformation fails; the facade writes the files |

`apps/benchmark/cli` compiles the discovery, settings, config, preparation and benchmark sources and runs the discovery, config and its own tests except `*ExampleFilesTest`. The `jca contract` workflow runs it on push and PR to those paths, weekly (`0 6 * * 1`), on Java 17, 21 and 25.
