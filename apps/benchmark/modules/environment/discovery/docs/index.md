# discovery

```
apps/benchmark/modules/environment/discovery/README.md : module summary and link to this index
apps/benchmark/modules/environment/discovery/build.gradle : Kotlin/JVM 17 library; api :jca and :environment:contract; :files (and its test fixtures) and :document; reads the keystore trial's catalogues through :document's catalogue/FamilyCatalogue
apps/benchmark/modules/environment/discovery/docs/index.md : this map
apps/benchmark/modules/environment/discovery/docs/keystore.md : the keystore trial: rows, StrongBox, refusal codes, cost
apps/benchmark/modules/environment/discovery/docs/probe.md : probe, trial and reuse behaviour
apps/benchmark/modules/environment/discovery/docs/requirements.md : the requirement trial: facts per type, rules, file fields
apps/benchmark/modules/environment/discovery/docs/security_contract.md : fields of probe_, trial_ and requirements_ files
apps/benchmark/modules/environment/discovery/src/main/kotlin/Discovery.kt : facade: probe, reusable, trial over one ProbeDirectory
apps/benchmark/modules/environment/discovery/src/main/kotlin/DiscoveryRun.kt : probe result: capture, capture file
apps/benchmark/modules/environment/discovery/src/main/kotlin/ReusedRun.kt : reusable result: capture and its files
apps/benchmark/modules/environment/discovery/src/main/kotlin/TrialFiles.kt : trial result: trial file, requirements file
apps/benchmark/modules/environment/discovery/src/main/kotlin/adapter/AttributeKind.kt : attribute name to LIST, INT, BOOL or STRING
apps/benchmark/modules/environment/discovery/src/main/kotlin/adapter/AttributeValueParser.kt : attribute value to its kind
apps/benchmark/modules/environment/discovery/src/main/kotlin/adapter/DeclaredAlias.kt : one Alg.Alias declaration and its target
apps/benchmark/modules/environment/discovery/src/main/kotlin/adapter/DeviceRuntimeReader.kt : RuntimeInfo from android.os.Build (reflective) and system properties
apps/benchmark/modules/environment/discovery/src/main/kotlin/adapter/PropertyKey.kt : sealed decoded property key
apps/benchmark/modules/environment/discovery/src/main/kotlin/adapter/PropertyKeyParser.kt : provider property name to PropertyKey
apps/benchmark/modules/environment/discovery/src/main/kotlin/adapter/PropertyMapIndex.kt : one provider's property map to meta, aliases, attributes
apps/benchmark/modules/environment/discovery/src/main/kotlin/adapter/ProviderProbe.kt : Provider[] to CapturedEnvironment
apps/benchmark/modules/environment/discovery/src/main/kotlin/adapter/ServiceKey.kt : case-folded (type, algorithm) key
apps/benchmark/modules/environment/discovery/src/main/kotlin/adapter/ServiceKeyException.kt : blank-field error for ServiceKey
apps/benchmark/modules/environment/discovery/src/main/kotlin/bundled/AliasedProvider.kt : delegating Provider under an alias; services re-bound to it
apps/benchmark/modules/environment/discovery/src/main/kotlin/bundled/BundledInstaller.kt : creates and appends each bundled provider; alias on a name clash
apps/benchmark/modules/environment/discovery/src/main/kotlin/bundled/BundledProvider.kt : one bundled provider spec {artifact, create, alias?}
apps/benchmark/modules/environment/discovery/src/main/kotlin/bundled/BundledProviderException.kt : coded install or spec error
apps/benchmark/modules/environment/discovery/src/main/kotlin/bundled/BundledProviders.kt : reads the bundledProviders list from a document map
apps/benchmark/modules/environment/discovery/src/main/kotlin/bundled/InstalledProvider.kt : registered name and artifact of one installed provider
apps/benchmark/modules/environment/discovery/src/main/kotlin/bundled/ProviderFactory.kt : Provider by reflection: no-argument constructor or static factory
apps/benchmark/modules/environment/discovery/src/main/kotlin/trial/DefaultRunTrial.kt : level 2: one real call per instantiated service or transformation
apps/benchmark/modules/environment/discovery/src/main/kotlin/trial/Outcomes.kt : TrialOutcome.of and failure, DefaultRunOutcome.failure: a thrown failure as its ErrorText
apps/benchmark/modules/environment/discovery/src/main/kotlin/trial/TransformationSet.kt : every declared mode x padding of a Cipher service
apps/benchmark/modules/environment/discovery/src/main/kotlin/trial/TrialRunner.kt : level 1: instantiate each captured service
apps/benchmark/modules/environment/discovery/src/main/kotlin/trial/call/ : per-type default calls, their registry, default keys, key candidates and key-generation specs from the catalogue and key bits, the one read-back of a spec (ParameterReadBack) for levels 2 and 3
apps/benchmark/modules/environment/discovery/src/main/kotlin/trial/keystore/KeystoreCatalogue.kt : the generator catalogues' keystore blocks, read through document's FamilyCatalogue: authorizations, trial key sizes and curves
apps/benchmark/modules/environment/discovery/src/main/kotlin/trial/keystore/KeystoreMaker.kt : what the keystore trial needs of a runtime: classes, StrongBox feature, generate, sweep, delete
apps/benchmark/modules/environment/discovery/src/main/kotlin/trial/keystore/KeystoreTrial.kt : level 4: one key per keystore-born generator, size or curve and hardware path, coded refusals
apps/benchmark/modules/environment/discovery/src/main/kotlin/trial/keystore/ReflectiveKeystore.kt : KeyGenParameterSpec by reflection, the provider's KeyStore, the StrongBox feature
apps/benchmark/modules/environment/discovery/src/main/kotlin/trial/requirement/AgreementFacts.kt : KeyAgreement facts
apps/benchmark/modules/environment/discovery/src/main/kotlin/trial/requirement/AliasRuns.kt : per declared alias: class run, same behaviour, own-name key
apps/benchmark/modules/environment/discovery/src/main/kotlin/trial/requirement/CallOrder.kt : one engine's real calls in order: setup once, operation per use; run, and written to the record
apps/benchmark/modules/environment/discovery/src/main/kotlin/trial/requirement/CipherBase.kt : the first key, spec and input a cipher runs on
apps/benchmark/modules/environment/discovery/src/main/kotlin/trial/requirement/CipherEffects.kt : which optional cipher argument changes the output
apps/benchmark/modules/environment/discovery/src/main/kotlin/trial/requirement/CipherEngine.kt : one cipher call: create, init, operate
apps/benchmark/modules/environment/discovery/src/main/kotlin/trial/requirement/CipherFacts.kt : Cipher facts
apps/benchmark/modules/environment/discovery/src/main/kotlin/trial/requirement/CipherReset.kt : a cipher's reset test per direction, on the base CipherFacts found
apps/benchmark/modules/environment/discovery/src/main/kotlin/trial/requirement/ClassRun.kt : the class a name really instantiates
apps/benchmark/modules/environment/discovery/src/main/kotlin/trial/requirement/DigestFacts.kt : MessageDigest facts
apps/benchmark/modules/environment/discovery/src/main/kotlin/trial/requirement/FactSheet.kt : facts in order, one guarded call each
apps/benchmark/modules/environment/discovery/src/main/kotlin/trial/requirement/FactoryFacts.kt : SecretKeyFactory facts
apps/benchmark/modules/environment/discovery/src/main/kotlin/trial/requirement/ForeignKeys.kt : the same key from every other provider
apps/benchmark/modules/environment/discovery/src/main/kotlin/trial/requirement/GeneratorFacts.kt : generator facts read from the default run
apps/benchmark/modules/environment/discovery/src/main/kotlin/trial/requirement/KeyOrigin.kt : keystore-born condition from a provider's measured refusals
apps/benchmark/modules/environment/discovery/src/main/kotlin/trial/requirement/KeySources.kt : candidate keys of a service, through the one cache
apps/benchmark/modules/environment/discovery/src/main/kotlin/trial/requirement/MacFacts.kt : Mac facts
apps/benchmark/modules/environment/discovery/src/main/kotlin/trial/requirement/PairSizes.kt : pair sizes the key sweep asks for
apps/benchmark/modules/environment/discovery/src/main/kotlin/trial/requirement/ParameterSpecs.kt : candidate specs and variations of an accepted one
apps/benchmark/modules/environment/discovery/src/main/kotlin/trial/requirement/ProbeKey.kt : one candidate key and where it came from
apps/benchmark/modules/environment/discovery/src/main/kotlin/trial/requirement/RequirementCall.kt : the per-type call and what it decided
apps/benchmark/modules/environment/discovery/src/main/kotlin/trial/requirement/RequirementCalls.kt : type to its requirement call
apps/benchmark/modules/environment/discovery/src/main/kotlin/trial/requirement/RequirementTrial.kt : level 3: one record per registered service
apps/benchmark/modules/environment/discovery/src/main/kotlin/trial/requirement/ResetRun.kt : one instance's operation twice and a new instance's once, untimed: resets, the refusing class or a coded reason
apps/benchmark/modules/environment/discovery/src/main/kotlin/trial/requirement/SignatureFacts.kt : Signature facts
apps/benchmark/modules/environment/discovery/src/main/kotlin/trial/requirement/Sweep.kt : an accepted set from single calls, as ranges
apps/benchmark/modules/environment/discovery/src/main/kotlin/write/EnvironmentYamlWriter.kt : writes probe_<utc>.yaml
apps/benchmark/modules/environment/discovery/src/main/kotlin/write/ProbeDirectory.kt : output directory: create-new, newest, sibling lookup
apps/benchmark/modules/environment/discovery/src/main/kotlin/write/RequirementYamlWriter.kt : writes requirements_<utc>.yaml
apps/benchmark/modules/environment/discovery/src/main/kotlin/write/TrialYamlWriter.kt : writes trial_<utc>.yaml
apps/benchmark/modules/environment/discovery/src/test/kotlin/BlockBytesTest.kt : byte goldens of the BLOCK codec: a capture-shaped document with an alias, a streamed requirements file
apps/benchmark/modules/environment/discovery/src/test/kotlin/BundledInstallerTest.kt : installer tests: reflection, append position, name clash, alias wrapper
apps/benchmark/modules/environment/discovery/src/test/kotlin/BundledProvidersTest.kt : bundled list reading and spec validation
apps/benchmark/modules/environment/discovery/src/test/kotlin/CaptureDocumentTest.kt : capture schema tests
apps/benchmark/modules/environment/discovery/src/test/kotlin/ContractsTest.kt : tests/contracts/yaml-codec/duplicate-key.yaml keeps its last value through this codec
apps/benchmark/modules/environment/discovery/src/test/kotlin/DefaultRunTrialTest.kt : default runs against the live JVM
apps/benchmark/modules/environment/discovery/src/test/kotlin/GeneratorKeysTest.kt : triedKeys: each size with its own key, a refusal, a pair asked no size above its default
apps/benchmark/modules/environment/discovery/src/test/kotlin/JcaContractTest.kt : JCA-surface drift checks on the running JVM
apps/benchmark/modules/environment/discovery/src/test/kotlin/KeyCandidatesTest.kt : key candidates: catalogued generators of the key type each with its registered spellings, then the key type, the names file's key size, then the entry's key-generation spec, generic names only uncatalogued, the raw key's name
apps/benchmark/modules/environment/discovery/src/test/kotlin/KeyGenerationSpecTest.kt : a keyGeneration row built and bound; builder, missing value, role mismatch, missing class and several recipes refused with their codes; a deviation's row only at its builds; DefaultKeys keeps one pair per spec
apps/benchmark/modules/environment/discovery/src/test/kotlin/KeyOrderTest.kt : every key candidate on the service's provider before another provider's
apps/benchmark/modules/environment/discovery/src/test/kotlin/KeystoreTrialTest.kt : keystore trial with a fake keystore: rows per size, curve and path, coded refusals, no StrongBox, absent section, bundled catalogue
apps/benchmark/modules/environment/discovery/src/test/kotlin/ProbeDirectoryTest.kt : no-overwrite test
apps/benchmark/modules/environment/discovery/src/test/kotlin/ProviderProbeTest.kt : ProviderProbe tests
apps/benchmark/modules/environment/discovery/src/test/kotlin/RecipeTreesContractTest.kt : tests/contracts/catalogue/recipe-trees.yaml: document's Recipes makes every recipe row's tree or refusal as Python's parameter_tree
apps/benchmark/modules/environment/discovery/src/test/kotlin/RequirementTrialTest.kt : requirement trial against the live JVM and made-up providers
apps/benchmark/modules/environment/discovery/src/test/kotlin/ResetRunTest.kt : reset test against the live JVM
apps/benchmark/modules/environment/discovery/src/test/kotlin/ReuseTest.kt : reusable tests
apps/benchmark/modules/environment/discovery/src/test/kotlin/ServiceAttributesTest.kt : ServiceAttributes tests
apps/benchmark/modules/environment/discovery/src/test/kotlin/ServiceKeyTest.kt : ServiceKey tests
apps/benchmark/modules/environment/discovery/src/test/kotlin/TrialDocumentTest.kt : trial schema tests
apps/benchmark/modules/environment/discovery/src/test/kotlin/TrialRunnerTest.kt : TrialRunner tests
```
