# config

```
apps/benchmark/modules/config/.gitignore : ignores /build
apps/benchmark/modules/config/README.md : module summary and link to this index
apps/benchmark/modules/config/build.gradle : Kotlin/JVM 17 library; snakeyaml 2.3 and :settings; passes examples.update to tests
apps/benchmark/modules/config/docs/config.md : authored files: global.yaml, test sets, rules, overrides, groups
apps/benchmark/modules/config/docs/generated.md : inventory.yaml, effective.yaml and report.yaml: build order, skips, warnings, errors
apps/benchmark/modules/config/docs/index.md : this map
apps/benchmark/modules/config/example/config_capture_example.yaml : example input capture
apps/benchmark/modules/config/example/config_effective_example.yaml : expected effective output
apps/benchmark/modules/config/example/config_global_example.yaml : example input global settings
apps/benchmark/modules/config/example/config_inventory_example.yaml : expected inventory output
apps/benchmark/modules/config/example/config_report_example.yaml : expected report output
apps/benchmark/modules/config/example/config_testset_example.yaml : example input test set
apps/benchmark/modules/config/example/config_trial_example.yaml : example input trial
apps/benchmark/modules/config/src/main/kotlin/AuthoredFiles.kt : a global.yaml and its test set through their parsers; nothing else read or written
apps/benchmark/modules/config/src/main/kotlin/Configuration.kt : facade: inventory, effective with its report, readEffective
apps/benchmark/modules/config/src/main/kotlin/effective/EffectiveBuilder.kt : global x test set x inventory x facts to EffectiveConfig
apps/benchmark/modules/config/src/main/kotlin/effective/EffectiveDocument.kt : effective.yaml schema
apps/benchmark/modules/config/src/main/kotlin/effective/LocatedMatch.kt : Rule.matches(Inventory.Located)
apps/benchmark/modules/config/src/main/kotlin/effective/OverrideResolver.kt : merges applicable overrides into one EffectiveEntry
apps/benchmark/modules/config/src/main/kotlin/effective/ReportDocument.kt : report.yaml schema
apps/benchmark/modules/config/src/main/kotlin/effective/SkipDocument.kt : one skip record as a map, shared by effective and report
apps/benchmark/modules/config/src/main/kotlin/effective/StoppedOnFailureException.kt : stop-policy failure carrying all skips
apps/benchmark/modules/config/src/main/kotlin/effective/dto/EffectiveConfig.kt : effective model; rejects an empty selection; run id from the capture name
apps/benchmark/modules/config/src/main/kotlin/effective/dto/EffectiveEntry.kt : one selected primitive's settings
apps/benchmark/modules/config/src/main/kotlin/effective/dto/EffectiveSource.kt : generatedFrom of effective.yaml
apps/benchmark/modules/config/src/main/kotlin/effective/dto/Report.kt : run id, warnings and skips of one effective build
apps/benchmark/modules/config/src/main/kotlin/effective/dto/Skip.kt : skip record {stage, provider?, type?, name?, reason}
apps/benchmark/modules/config/src/main/kotlin/entry/EntryKeys.kt : per-primitive key names shared by test-set overrides and effective entries
apps/benchmark/modules/config/src/main/kotlin/global/AnalysisDocument.kt : analysis section reader and writer
apps/benchmark/modules/config/src/main/kotlin/global/GlobalDocument.kt : global.yaml schema
apps/benchmark/modules/config/src/main/kotlin/global/PolicyDocument.kt : policy section reader and writer
apps/benchmark/modules/config/src/main/kotlin/global/ProvidersDocument.kt : providers section reader and writer; bundled list shared with effective
apps/benchmark/modules/config/src/main/kotlin/global/RunDocument.kt : run section reader and writer
apps/benchmark/modules/config/src/main/kotlin/global/ThermalGateDocument.kt : run.thermalGate reader and writer
apps/benchmark/modules/config/src/main/kotlin/global/dto/AnalysisSettings.kt : analysis defaults and validation: charts, dir, statistic, display units
apps/benchmark/modules/config/src/main/kotlin/global/dto/BundledProvider.kt : one bundled provider and its validation: artifact, create, alias
apps/benchmark/modules/config/src/main/kotlin/global/dto/GlobalConfig.kt : global model
apps/benchmark/modules/config/src/main/kotlin/global/dto/MeasurePass.kt : one run.passes entry: name timing, energy or allocation, samples >= 1
apps/benchmark/modules/config/src/main/kotlin/global/dto/Policy.kt : onFailure enum STOP, SKIP
apps/benchmark/modules/config/src/main/kotlin/global/dto/ProviderSources.kt : providers section model; no duplicate artifact or alias
apps/benchmark/modules/config/src/main/kotlin/global/dto/RunSettings.kt : run defaults and validation
apps/benchmark/modules/config/src/main/kotlin/global/dto/Selection.kt : testSet and global excludes
apps/benchmark/modules/config/src/main/kotlin/global/dto/ThermalGate.kt : run.thermalGate defaults and validation: sensors, margin, poll, timeout
apps/benchmark/modules/config/src/main/kotlin/global/dto/Warmup.kt : run.warmup defaults and validation: iterations, jobs
apps/benchmark/modules/config/src/main/kotlin/inventory/InventoryBuilder.kt : capture x trial to inventory
apps/benchmark/modules/config/src/main/kotlin/inventory/InventoryDocument.kt : inventory.yaml schema
apps/benchmark/modules/config/src/main/kotlin/inventory/InventorySourceDocument.kt : capture, trial, device block shared by both generated files
apps/benchmark/modules/config/src/main/kotlin/inventory/dto/Inventory.kt : inventory model with its build warnings; rejects two spellings of one canonical name
apps/benchmark/modules/config/src/main/kotlin/inventory/dto/InventoryEntry.kt : one observed primitive
apps/benchmark/modules/config/src/main/kotlin/inventory/dto/InventorySource.kt : inventory provenance
apps/benchmark/modules/config/src/main/kotlin/names/AlgorithmNames.kt : algorithm-names.yaml reader: canonical name and key size, rule name match, identifier fold
apps/benchmark/modules/config/src/main/kotlin/names/dto/Canonical.kt : canonical name, key-size constraint, catalogued or not
apps/benchmark/modules/config/src/main/kotlin/source/CaptureSource.kt : reads a discovery capture file as CaptureView
apps/benchmark/modules/config/src/main/kotlin/source/CaptureView.kt : capture fields config uses
apps/benchmark/modules/config/src/main/kotlin/source/TrialSource.kt : reads a discovery trial file as TrialView
apps/benchmark/modules/config/src/main/kotlin/source/TrialView.kt : trial fields config uses
apps/benchmark/modules/config/src/main/kotlin/testset/RuleDocument.kt : rule {provider, type, name, group} reader and writer
apps/benchmark/modules/config/src/main/kotlin/testset/TestSetDocument.kt : test-set schema
apps/benchmark/modules/config/src/main/kotlin/testset/dto/Override.kt : one override and its validation
apps/benchmark/modules/config/src/main/kotlin/testset/dto/Rule.kt : rule matching through AlgorithmNames, and specificity
apps/benchmark/modules/config/src/main/kotlin/testset/dto/TestSet.kt : test-set model
apps/benchmark/modules/config/src/main/kotlin/yaml/DocumentFields.kt : typed reads, expectKeys, path-annotated failures
apps/benchmark/modules/config/src/main/kotlin/yaml/DocumentHandler.kt : reader and writer interface
apps/benchmark/modules/config/src/main/kotlin/yaml/DocumentReader.kt : reader interface with schemaVersion
apps/benchmark/modules/config/src/main/kotlin/yaml/ProviderTree.kt : provider to type to name map, both directions
apps/benchmark/modules/config/src/main/kotlin/yaml/ReadOnlyYamlFile.kt : read with missing, parse and schemaVersion checks
apps/benchmark/modules/config/src/main/kotlin/yaml/YamlCodec.kt : SafeConstructor YAML, duplicate keys refused
apps/benchmark/modules/config/src/main/kotlin/yaml/YamlFile.kt : stamped schemaVersion and .partial atomic write
apps/benchmark/modules/config/src/main/kotlin/yaml/YamlFiles.kt : factory for YamlFile and ReadOnlyYamlFile
apps/benchmark/modules/config/src/main/resources/algorithm-names.yaml : canonical name per spelling and engine type; owned here, perf-repair keeps a copy its tests compare
apps/benchmark/modules/config/src/test/kotlin/AlgorithmNamesTest.kt : the cases shared with perf-repair, every catalogued spelling, inventory duplicates, rule names
apps/benchmark/modules/config/src/test/kotlin/AuthoredFilesTest.kt : a typo key or a bad providers.bundled stops the parse-only read
apps/benchmark/modules/config/src/test/kotlin/CommittedConfigTest.kt : committed config/ files parse
apps/benchmark/modules/config/src/test/kotlin/ConfigurationTest.kt : facade tests
apps/benchmark/modules/config/src/test/kotlin/DocumentFixture.kt : built documents shared by the schema tests
apps/benchmark/modules/config/src/test/kotlin/DocumentRoundTripTest.kt : every document round-trips; schemaVersion stamp and check
apps/benchmark/modules/config/src/test/kotlin/EffectiveBuilderTest.kt : selection, policy and facts tests
apps/benchmark/modules/config/src/test/kotlin/EffectiveConfigTest.kt : run id tests
apps/benchmark/modules/config/src/test/kotlin/ExampleFilesTest.kt : example inputs must produce the committed outputs
apps/benchmark/modules/config/src/test/kotlin/Fixtures.kt : shared test fixtures
apps/benchmark/modules/config/src/test/kotlin/GlobalDocumentTest.kt : global.yaml analysis section tests
apps/benchmark/modules/config/src/test/kotlin/InventoryBuilderTest.kt : inventory tests
apps/benchmark/modules/config/src/test/kotlin/MalformedDocumentsTest.kt : malformed documents refused by name
apps/benchmark/modules/config/src/test/kotlin/OverrideResolverTest.kt : override precedence tests
apps/benchmark/modules/config/src/test/kotlin/RuleTest.kt : rule matching tests
apps/benchmark/modules/config/src/test/resources/algorithm-names-cases.yaml : name cases both readers resolve alike; owned here, perf-repair keeps a copy its tests compare
```
