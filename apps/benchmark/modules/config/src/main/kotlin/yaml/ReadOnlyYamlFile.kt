package io.github.junekim0007.cryptobench.config.yaml

import io.github.junekim0007.cryptobench.document.SchemaVersion
import io.github.junekim0007.cryptobench.document.YamlCodec
import org.yaml.snakeyaml.error.YAMLException
import java.io.File

class ReadOnlyYamlFile<T> internal constructor(
    val file: File,
    private val reader: DocumentReader<T>,
    private val codec: YamlCodec,
) {

    fun read(): T {
        if (!file.isFile) {
            throw IllegalArgumentException("missing_file: ${file.path}")
        }
        val document = try {
            codec.load(file.readText())
        } catch (failure: YAMLException) {
            throw IllegalArgumentException("unreadable_yaml: ${file.name}: ${failure.message}", failure)
        }
        SchemaVersion.require(document, reader.schemaVersion, file.name)
        return try {
            reader.parse(document)
        } catch (failure: IllegalArgumentException) {
            throw IllegalArgumentException("${file.name}: ${failure.message}", failure)
        }
    }

    internal companion object {
        const val SCHEMA_VERSION = "schemaVersion"
    }
}
