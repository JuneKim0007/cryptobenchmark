package io.github.junekim0007.cryptobench.config.yaml

import java.io.File
import java.io.IOException
import java.nio.file.Files
import java.nio.file.StandardOpenOption

/**
 * One YAML file of one kind. Owns what every kind shares: loading, dumping, the `schemaVersion` check and
 * stamp, directory creation, overwriting. A handler only maps its own fields.
 */
class YamlFile<T> internal constructor(
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

    fun write(value: T): File {
        val handler = reader as? DocumentHandler<T> ?: throw UnsupportedOperationException("read_only: ${file.name}")
        val directory = file.absoluteFile.parentFile
        if (!directory.exists() && !directory.mkdirs()) {
            throw IOException("cannot create ${directory.absolutePath}")
        }
        val document = linkedMapOf<String, Any>(SCHEMA_VERSION to handler.schemaVersion)
        document.putAll(handler.of(value))
        Files.write(file.toPath(), codec.dump(document).toByteArray(Charsets.UTF_8),
            StandardOpenOption.CREATE, StandardOpenOption.TRUNCATE_EXISTING, StandardOpenOption.WRITE)
        return file
    }

    private companion object {
        const val SCHEMA_VERSION = "schemaVersion"
    }
}
