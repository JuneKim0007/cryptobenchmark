# config

```
modules/config/.gitignore : ignores /build
modules/config/README.md : module summary and link to this index
modules/config/build.gradle : Kotlin/JVM 17 library; snakeyaml 2.3 and :settings; perf-repair's algorithm-names.yaml as a resource; passes examples.update to tests
modules/config/docs/config.md : authored files: global.yaml, test sets, rules, overrides, groups
modules/config/docs/generated.md : inventory.yaml, effective.yaml and report.yaml: build order, skips, warnings, errors
modules/config/docs/index.md : this map
modules/config/example/config_capture_example.yaml : example input capture
modules/config/example/config_effective_example.yaml : expected effective output
modules/config/example/config_global_example.yaml : example input global settings
modules/config/example/config_inventory_example.yaml : expected inventory output
modules/config/example/config_report_example.yaml : expected report output
modules/config/example/config_testset_example.yaml : example input test set
modules/config/example/config_trial_example.yaml : example input trial
modules/config/src/main/kotlin/Configuration.kt : facade: inventory, effective with its report, readEffective
modules/config/src/main/kotlin/effective/EffectiveBuilder.kt : global x test set x inventory x facts to EffectiveConfig
modules/config/src/main/kotlin/effective/EffectiveDocument.kt : effective.yaml schema
modules/config/src/main/kotlin/effective/LocatedMatch.kt : Rule.matches(Inventory.Located)
modules/config/src/main/kotlin/effective/OverrideResolver.kt : merges applicable overrides into one EffectiveEntry
modules/config/src/main/kotlin/effective/ReportDocument.kt : report.yaml schema
modules/config/src/main/kotlin/effective/SkipDocument.kt : one skip record as a map, shared by effective and report
modules/config/src/main/kotlin/effective/StoppedOnFailureException.kt : stop-policy failure carrying all skips
modules/config/src/main/kotlin/effective/dto/EffectiveConfig.kt : effective model; rejects an empty selection; run id from the capture name
modules/config/src/main/kotlin/effective/dto/EffectiveEntry.kt : one selected primitive's settings
modules/config/src/main/kotlin/effective/dto/EffectiveSource.kt : generatedFrom of effective.yaml
modules/config/src/main/kotlin/effective/dto/Report.kt : run id, warnings and skips of one effective build
modules/config/src/main/kotlin/effective/dto/Skip.kt : skip record {stage, provider?, type?, name?, reason}
modules/config/src/main/kotlin/entry/EntryKeys.kt : per-primitive key names shared by test-set overrides and effective entries
modules/config/src/main/kotlin/global/AnalysisDocument.kt : analysis section reader and writer
modules/config/src/main/kotlin/global/GlobalDocument.kt : global.yaml schema
modules/config/src/main/kotlin/global/PolicyDocument.kt : policy section reader and writer
modules/config/src/main/kotlin/global/ProvidersDocument.kt : providers section reader and writer; bundled list shared with effective
modules/config/src/main/kotlin/global/RunDocument.kt : run section reader and writer
modules/config/src/main/kotlin/global/dto/AnalysisSettings.kt : analysis defaults and validation: charts, dir, statistic, display units
modules/config/src/main/kotlin/global/dto/BundledProvider.kt : one bundled provider and its validation: artifact, create, alias
modules/config/src/main/kotlin/global/dto/GlobalConfig.kt : global model
modules/config/src/main/kotlin/global/dto/Policy.kt : onFailure enum STOP, SKIP
modules/config/src/main/kotlin/global/dto/ProviderSources.kt : providers section model; no duplicate artifact or alias
modules/config/src/main/kotlin/global/dto/RunSettings.kt : run defaults and validation
modules/config/src/main/kotlin/global/dto/Selection.kt : testSet and global excludes
modules/config/src/main/kotlin/inventory/InventoryBuilder.kt : capture x trial to inventory
modules/config/src/main/kotlin/inventory/InventoryDocument.kt : inventory.yaml schema
modules/config/src/main/kotlin/inventory/InventorySourceDocument.kt : capture, trial, device block shared by both generated files
modules/config/src/main/kotlin/inventory/dto/Inventory.kt : inventory model; rejects two spellings of one canonical name
modules/config/src/main/kotlin/inventory/dto/InventoryEntry.kt : one observed primitive
modules/config/src/main/kotlin/inventory/dto/InventorySource.kt : inventory provenance
modules/config/src/main/kotlin/names/AlgorithmNames.kt : algorithm-names.yaml reader: canonical name and key size, rule name match, identifier fold
modules/config/src/main/kotlin/names/dto/Canonical.kt : canonical name, key-size constraint, catalogued or not
modules/config/src/main/kotlin/source/CaptureSource.kt : reads a discovery capture file as CaptureView
modules/config/src/main/kotlin/source/CaptureView.kt : capture fields config uses
modules/config/src/main/kotlin/source/TrialSource.kt : reads a discovery trial file as TrialView
modules/config/src/main/kotlin/source/TrialView.kt : trial fields config uses
modules/config/src/main/kotlin/testset/RuleDocument.kt : rule {provider, type, name, group} reader and writer
modules/config/src/main/kotlin/testset/TestSetDocument.kt : test-set schema
modules/config/src/main/kotlin/testset/dto/Override.kt : one override and its validation
modules/config/src/main/kotlin/testset/dto/Rule.kt : rule matching through AlgorithmNames, and specificity
modules/config/src/main/kotlin/testset/dto/TestSet.kt : test-set model
modules/config/src/main/kotlin/yaml/DocumentFields.kt : typed reads, expectKeys, path-annotated failures
modules/config/src/main/kotlin/yaml/DocumentHandler.kt : reader and writer interface
modules/config/src/main/kotlin/yaml/DocumentReader.kt : reader interface with schemaVersion
modules/config/src/main/kotlin/yaml/ProviderTree.kt : provider to type to name map, both directions
modules/config/src/main/kotlin/yaml/ReadOnlyYamlFile.kt : read with missing, parse and schemaVersion checks
modules/config/src/main/kotlin/yaml/YamlCodec.kt : SafeConstructor YAML, duplicate keys refused
modules/config/src/main/kotlin/yaml/YamlFile.kt : stamped schemaVersion and .partial atomic write
modules/config/src/main/kotlin/yaml/YamlFiles.kt : factory for YamlFile and ReadOnlyYamlFile
modules/config/src/test/kotlin/AlgorithmNamesTest.kt : the cases shared with perf-repair, every catalogued spelling, inventory duplicates, rule names
modules/config/src/test/kotlin/CommittedConfigTest.kt : committed config/ files parse
modules/config/src/test/kotlin/ConfigurationTest.kt : facade tests
modules/config/src/test/kotlin/DocumentFixture.kt : built documents shared by the schema tests
modules/config/src/test/kotlin/DocumentRoundTripTest.kt : every document round-trips; schemaVersion stamp and check
modules/config/src/test/kotlin/EffectiveBuilderTest.kt : selection, policy and facts tests
modules/config/src/test/kotlin/EffectiveConfigTest.kt : run id tests
modules/config/src/test/kotlin/ExampleFilesTest.kt : example inputs must produce the committed outputs
modules/config/src/test/kotlin/Fixtures.kt : shared test fixtures
modules/config/src/test/kotlin/GlobalDocumentTest.kt : global.yaml analysis section tests
modules/config/src/test/kotlin/InventoryBuilderTest.kt : inventory tests
modules/config/src/test/kotlin/MalformedDocumentsTest.kt : malformed documents refused by name
modules/config/src/test/kotlin/OverrideResolverTest.kt : override precedence tests
modules/config/src/test/kotlin/RuleTest.kt : rule matching tests
```
