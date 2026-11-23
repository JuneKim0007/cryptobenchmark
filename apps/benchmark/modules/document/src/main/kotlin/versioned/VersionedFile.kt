package io.github.junekim0007.cryptobench.document.versioned

import io.github.junekim0007.cryptobench.document.SchemaVersion
import io.github.junekim0007.cryptobench.document.YamlCodec
import org.yaml.snakeyaml.error.YAMLException
import java.io.File

/** The fixed steps of a versioned read: present, loadable, the version this build reads, then the reader's parse. */
class VersionedFile<T> internal constructor(
    val file: File,
    private val reader: DocumentReader<T>,
    private val codec: YamlCodec,
) {

    fun read(): T {
        if (!file.isFile) {
            throw IllegalArgumentException("missing_file: ${file.path}")
        }
        return read(file.readText())
    }

    fun read(text: String): T {
        val document = try {
            codec.load(text)
        } catch (failure: YAMLException) {
            throw IllegalArgumentException(FileRefusal.of(file.name, "unreadable_yaml: ${failure.message}"), failure)
        } catch (failure: IllegalArgumentException) {
            throw IllegalArgumentException(FileRefusal.of(file.name, failure.message.orEmpty()), failure)
        }
        SchemaVersion.require(document, reader.schemaVersion, file.name)
        return try {
            reader.parse(document)
        } catch (failure: IllegalArgumentException) {
            throw IllegalArgumentException(FileRefusal.of(file.name, failure.message.orEmpty()), failure)
        }
    }
}
