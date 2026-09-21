package io.github.junekim0007.cryptobench.config.yaml

import java.io.File

class ReadOnlyYamlFile<T> internal constructor(
    val file: File,
    private val reader: DocumentReader<T>,
    private val codec: YamlCodec,
) {

    fun read(): T {
        val document = try {
            codec.load(file.readText())
        } catch (failure: RuntimeException) {
            throw IllegalArgumentException("unreadable_yaml: ${file.name}: ${failure.message}", failure)
        }
        val version = document[SCHEMA_VERSION] as? Number ?: throw IllegalArgumentException("missing_field: ${file.name}: $SCHEMA_VERSION")
        require(version.toInt() == reader.schemaVersion) {
            "unsupported_schema_version: ${file.name}: $version, this build reads ${reader.schemaVersion}"
        }
        return reader.parse(document)
    }

    internal companion object {
        const val SCHEMA_VERSION = "schemaVersion"
    }
}
