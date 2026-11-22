# document

```
apps/benchmark/modules/document/README.md : module summary and link to this index
apps/benchmark/modules/document/build.gradle : Kotlin/JVM 17 library; snakeyaml 2.3; in the root build it alone carries the family catalogues, provider-builds.yaml, deviations.yaml and groups.yaml beside catalogue/FamilyCatalogue, and algorithm-names.yaml beside names/AlgorithmNames, through gradle/guide-resources.gradle
apps/benchmark/modules/document/docs/index.md : this map
apps/benchmark/modules/document/src/main/kotlin/AtomicFile.kt : whole-or-nothing write: a unique temporary file beside the target, renamed over it; replace = false refuses an existing file
apps/benchmark/modules/document/src/main/kotlin/DocumentFields.kt : typed reads with missing_field and wrong_type; optionalSection (null) and sectionOrEmpty; optionalSections and sectionsIfKeyPresent (a null value fails); choice by key (invalid:) and by enum (unknown_<field>:); expectKeys
apps/benchmark/modules/document/src/main/kotlin/ErrorCode.kt : the one Kotlin error-code pattern; FileRefusal and records' Skip check codes with it
apps/benchmark/modules/document/src/main/kotlin/SchemaVersion.kt : the one schemaVersion refusal: missing_field: <name>: schemaVersion, unsupported_schema_version: <name>: <v>, this build reads <n>
apps/benchmark/modules/document/src/main/kotlin/YamlCodec.kt : SnakeYAML dump and load by profile: DOCUMENT (config, preparation, benchmark's YAML files: AUTO, aliases dereferenced, safe, duplicate keys and non-mappings refused), CAPTURE (discovery: BLOCK, aliases kept, default constructor, unchecked mapping cast), RESULTS (benchmark's androidx JSON, energy and pass inputs: safe, duplicate keys last wins, not_a_mapping: <value>)
apps/benchmark/modules/document/src/main/kotlin/YamlLine.kt : a double-quoted YAML scalar for line-at-a-time writers (cpu-pins.yaml, energy-dry.yaml)
apps/benchmark/modules/document/src/main/kotlin/catalogue/CatalogueOverlays.kt : provider-builds.yaml and deviations.yaml: per build what a provider-wide behaviour (only where the entry has the field's parent) or a deviation states of an entry; a provider's build on a platform: exact, else the nearest at or below of its kind, else its latest
apps/benchmark/modules/document/src/main/kotlin/catalogue/FamilyCatalogue.kt : the one Kotlin reader of algorithms/<family>_catalogue.yaml: entries by type and any spelling of the name (through AlgorithmNames), one build's view (the entry's own providers section over the overlays, only for an entry with a providers section, as the Python reader), the guide files beside it (missing_resource); no validation, the Python reader validates
apps/benchmark/modules/document/src/main/kotlin/catalogue/GroupExemplars.kt : groups.yaml's exemplars per family, in file order
apps/benchmark/modules/document/src/main/kotlin/catalogue/Overrides.kt : a build's path: value on a copy of an entry: a dotted field (a list step by name or fact), or a whole required or optional row (null drops it)
apps/benchmark/modules/document/src/main/kotlin/names/AlgorithmNames.kt : the one Kotlin reader of algorithm-names.yaml (beside it): canonical name and key size, key type, rule name match, identifier fold; refuses a spelling under two names, sized and named, or an OID. form apart from its bare OID
apps/benchmark/modules/document/src/main/kotlin/names/dto/Canonical.kt : canonical name, key-size constraint, catalogued or not
apps/benchmark/modules/document/src/main/kotlin/versioned/DocumentHandler.kt : reader and writer interface
apps/benchmark/modules/document/src/main/kotlin/versioned/DocumentReader.kt : reader interface: the schemaVersion it reads and its parse
apps/benchmark/modules/document/src/main/kotlin/versioned/FileRefusal.kt : a reader's <code>: <rest> refusal with the file after its code: <code>: <file>: <rest>; a codeless one is invalid: refusal without a code: <file>: <message>
apps/benchmark/modules/document/src/main/kotlin/versioned/MapDocument.kt : a versioned document written as the map its writer built (check.yaml, interop.yaml)
apps/benchmark/modules/document/src/main/kotlin/versioned/VersionedFile.kt : the one versioned read, of a file or its text: missing_file, unreadable_yaml: <file>, the SchemaVersion refusal, then the reader's parse with its refusal as <code>: <file>: <rest> (FileRefusal)
apps/benchmark/modules/document/src/main/kotlin/versioned/YamlFile.kt : VersionedFile's read; write stamps schemaVersion first, through AtomicFile
apps/benchmark/modules/document/src/main/kotlin/versioned/YamlFiles.kt : factory for YamlFile and VersionedFile on one codec profile
apps/benchmark/modules/document/src/test/kotlin/DocumentFieldsTest.kt : sectionsIfKeyPresent fails on a null value, optionalSections, optionalSection and sectionOrEmpty on absent and null
apps/benchmark/modules/document/src/test/kotlin/DocumentIoTest.kt : SchemaVersion refusals, a parse refusal as <code>: <file>: <rest> (codeless, empty and colon-in-detail cases), AtomicFile replace and refuse, YamlLine escapes
apps/benchmark/modules/document/src/test/kotlin/FamilyCatalogueTest.kt : a build's view with behaviours, deviations and the entry's own section, an entry without providers untouched, the nearest build, group exemplars
apps/benchmark/modules/document/src/test/kotlin/YamlCodecTest.kt : both profiles' dump style and load failures
```
