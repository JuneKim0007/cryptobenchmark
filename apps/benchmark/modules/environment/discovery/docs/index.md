# discovery

```
apps/benchmark/modules/environment/discovery/.gitignore : ignores /build
apps/benchmark/modules/environment/discovery/README.md : module summary and link to this index
apps/benchmark/modules/environment/discovery/build.gradle : Kotlin/JVM 17 library; snakeyaml 2.3; passes examples.update to tests
apps/benchmark/modules/environment/discovery/docs/index.md : this map
apps/benchmark/modules/environment/discovery/docs/probe.md : probe, trial and reuse behaviour
apps/benchmark/modules/environment/discovery/docs/security_contract.md : fields of probe_, probe_classes_ and trial_ files
apps/benchmark/modules/environment/discovery/example/discovery_capture_example.yaml : sample probe_<utc>.yaml (SUN, SunJCE)
apps/benchmark/modules/environment/discovery/example/discovery_trial_example.yaml : sample trial_<utc>.yaml for the same capture
apps/benchmark/modules/environment/discovery/src/main/kotlin/Discovery.kt : facade: probe, reusable, trial over one ProbeDirectory
apps/benchmark/modules/environment/discovery/src/main/kotlin/DiscoveryRun.kt : probe result: capture, capture file, classes file
apps/benchmark/modules/environment/discovery/src/main/kotlin/ReusedRun.kt : reusable result: capture and its three files
apps/benchmark/modules/environment/discovery/src/main/kotlin/adapter/AttributeKind.kt : attribute name to LIST, INT, BOOL or STRING
apps/benchmark/modules/environment/discovery/src/main/kotlin/adapter/AttributeValueParser.kt : attribute value to its kind
apps/benchmark/modules/environment/discovery/src/main/kotlin/adapter/DeclaredAlias.kt : one Alg.Alias declaration and its target
apps/benchmark/modules/environment/discovery/src/main/kotlin/adapter/DeviceRuntimeReader.kt : RuntimeInfo from android.os.Build (reflective) and system properties
apps/benchmark/modules/environment/discovery/src/main/kotlin/adapter/PropertyKey.kt : sealed decoded property key
apps/benchmark/modules/environment/discovery/src/main/kotlin/adapter/PropertyKeyParser.kt : provider property name to PropertyKey
apps/benchmark/modules/environment/discovery/src/main/kotlin/adapter/PropertyMapIndex.kt : one provider's property map to meta, aliases, attributes
apps/benchmark/modules/environment/discovery/src/main/kotlin/adapter/ProviderProbe.kt : Provider[] to CapturedEnvironment
apps/benchmark/modules/environment/discovery/src/main/kotlin/bundled/AliasedProvider.kt : delegating Provider under an alias; services re-bound to it
apps/benchmark/modules/environment/discovery/src/main/kotlin/bundled/BundledInstaller.kt : creates and appends each bundled provider; alias on a name clash
apps/benchmark/modules/environment/discovery/src/main/kotlin/bundled/BundledProvider.kt : one bundled provider spec {artifact, create, alias?}
apps/benchmark/modules/environment/discovery/src/main/kotlin/bundled/BundledProviderException.kt : coded install or spec error
apps/benchmark/modules/environment/discovery/src/main/kotlin/bundled/BundledProviders.kt : reads the bundledProviders list from a document map
apps/benchmark/modules/environment/discovery/src/main/kotlin/bundled/InstalledProvider.kt : registered name and artifact of one installed provider
apps/benchmark/modules/environment/discovery/src/main/kotlin/bundled/ProviderFactory.kt : Provider by reflection: no-argument constructor or static factory
apps/benchmark/modules/environment/discovery/src/main/kotlin/contract/AliasEntry.kt : unresolved alias record
apps/benchmark/modules/environment/discovery/src/main/kotlin/contract/CapturedEnvironment.kt : capture model, SCHEMA_VERSION 1
apps/benchmark/modules/environment/discovery/src/main/kotlin/contract/DefaultRunOutcome.kt : one default-run result
apps/benchmark/modules/environment/discovery/src/main/kotlin/contract/ProviderEntry.kt : one provider record with origin and artifact
apps/benchmark/modules/environment/discovery/src/main/kotlin/contract/ProviderOrigin.kt : platform or bundled
apps/benchmark/modules/environment/discovery/src/main/kotlin/contract/RuntimeInfo.kt : device and runtime provenance
apps/benchmark/modules/environment/discovery/src/main/kotlin/contract/ServiceAttributes.kt : typed view of a service's declared attributes
apps/benchmark/modules/environment/discovery/src/main/kotlin/contract/ServiceEntry.kt : one service record
apps/benchmark/modules/environment/discovery/src/main/kotlin/contract/ServiceKey.kt : case-folded (type, algorithm) key
apps/benchmark/modules/environment/discovery/src/main/kotlin/contract/ServiceKeyException.kt : blank-field error for ServiceKey
apps/benchmark/modules/environment/discovery/src/main/kotlin/contract/ServiceTrialEntry.kt : trial result for one service
apps/benchmark/modules/environment/discovery/src/main/kotlin/contract/TransformationTrialEntry.kt : trial result for one cipher transformation
apps/benchmark/modules/environment/discovery/src/main/kotlin/contract/TrialOutcome.kt : instantiation success or error
apps/benchmark/modules/environment/discovery/src/main/kotlin/contract/TrialReport.kt : trial model, SCHEMA_VERSION 3
apps/benchmark/modules/environment/discovery/src/main/kotlin/query/ServiceIndex.kt : one provider's services by name or alias
apps/benchmark/modules/environment/discovery/src/main/kotlin/query/TransformationFailure.kt : one failed transformation row
apps/benchmark/modules/environment/discovery/src/main/kotlin/trial/Attempt.kt : runs a block, maps Exception or LinkageError to TrialOutcome
apps/benchmark/modules/environment/discovery/src/main/kotlin/trial/DefaultRunTrial.kt : level 2: one real call per instantiated service or transformation
apps/benchmark/modules/environment/discovery/src/main/kotlin/trial/TransformationSet.kt : bare algorithm plus every declared mode x padding
apps/benchmark/modules/environment/discovery/src/main/kotlin/trial/TrialRunner.kt : level 1: instantiate each captured service
apps/benchmark/modules/environment/discovery/src/main/kotlin/trial/call/ : per-type default calls, their registry, default keys, key names and key bits
apps/benchmark/modules/environment/discovery/src/main/kotlin/write/CaptureDocument.kt : capture YAML schema (of, parse)
apps/benchmark/modules/environment/discovery/src/main/kotlin/write/DocumentFields.kt : typed reads of document keys
apps/benchmark/modules/environment/discovery/src/main/kotlin/write/EnvironmentYamlWriter.kt : writes probe_<utc>.yaml
apps/benchmark/modules/environment/discovery/src/main/kotlin/write/ProbeDirectory.kt : output directory: create-new, newest, sibling lookup
apps/benchmark/modules/environment/discovery/src/main/kotlin/write/ProbeFileName.kt : <prefix>_<yyyyMMddTHHmmssZ>.yaml naming
apps/benchmark/modules/environment/discovery/src/main/kotlin/write/ProviderClassNameWriter.kt : writes probe_classes_<utc>.yaml
apps/benchmark/modules/environment/discovery/src/main/kotlin/write/TrialDocument.kt : trial YAML schema (of, parse)
apps/benchmark/modules/environment/discovery/src/main/kotlin/write/TrialYamlWriter.kt : writes trial_<utc>.yaml
apps/benchmark/modules/environment/discovery/src/main/kotlin/write/YamlCodec.kt : snakeyaml dump and load, block style, indent 2
apps/benchmark/modules/environment/discovery/src/test/kotlin/BundledInstallerTest.kt : installer tests: reflection, append position, name clash, alias wrapper
apps/benchmark/modules/environment/discovery/src/test/kotlin/BundledProvidersTest.kt : bundled list reading and spec validation
apps/benchmark/modules/environment/discovery/src/test/kotlin/CaptureDocumentTest.kt : capture schema tests
apps/benchmark/modules/environment/discovery/src/test/kotlin/DefaultRunTrialTest.kt : default runs against the live JVM
apps/benchmark/modules/environment/discovery/src/test/kotlin/JcaContractTest.kt : JCA-surface drift checks on the running JVM
apps/benchmark/modules/environment/discovery/src/test/kotlin/KeyNamesTest.kt : KeyNames tests
apps/benchmark/modules/environment/discovery/src/test/kotlin/ProbeDirectoryTest.kt : no-overwrite test
apps/benchmark/modules/environment/discovery/src/test/kotlin/ProviderProbeTest.kt : ProviderProbe tests
apps/benchmark/modules/environment/discovery/src/test/kotlin/ReuseTest.kt : reusable tests
apps/benchmark/modules/environment/discovery/src/test/kotlin/ServiceKeyTest.kt : ServiceKey tests
apps/benchmark/modules/environment/discovery/src/test/kotlin/TrialDocumentTest.kt : trial schema tests
apps/benchmark/modules/environment/discovery/src/test/kotlin/TrialRunnerTest.kt : TrialRunner tests
apps/benchmark/modules/environment/discovery/src/test/kotlin/YamlCodecTest.kt : YamlCodec tests
```
