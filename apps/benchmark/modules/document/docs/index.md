# document

```
apps/benchmark/modules/document/.gitignore : ignores /build
apps/benchmark/modules/document/README.md : module summary and link to this index
apps/benchmark/modules/document/build.gradle : Kotlin/JVM 17 library; snakeyaml 2.3
apps/benchmark/modules/document/docs/index.md : this map
apps/benchmark/modules/document/src/main/kotlin/DocumentFields.kt : typed reads with missing_field and wrong_type; optionalSection (null) and sectionOrEmpty; optionalSections and sectionsIfKeyPresent (a null value fails); choice by key (invalid:) and by enum (unknown_<field>:); expectKeys
apps/benchmark/modules/document/src/main/kotlin/YamlCodec.kt : SnakeYAML dump and load by profile: DOCUMENT (config, preparation: AUTO, aliases dereferenced, safe, duplicate keys and non-mappings refused), CAPTURE (discovery: BLOCK, aliases kept, default constructor, unchecked mapping cast)
apps/benchmark/modules/document/src/test/kotlin/DocumentFieldsTest.kt : sectionsIfKeyPresent fails on a null value, optionalSections, optionalSection and sectionOrEmpty on absent and null
apps/benchmark/modules/document/src/test/kotlin/YamlCodecTest.kt : both profiles' dump style and load failures
```
