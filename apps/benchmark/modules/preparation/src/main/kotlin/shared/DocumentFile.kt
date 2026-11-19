package io.github.junekim0007.cryptobench.preparation.shared

import io.github.junekim0007.cryptobench.document.AtomicFile
import io.github.junekim0007.cryptobench.document.SchemaVersion
import io.github.junekim0007.cryptobench.document.YamlCodec
import org.yaml.snakeyaml.error.YAMLException
import java.io.File

object DocumentFile {

    fun read(file: File, supportedSchemaVersion: Int): Map<String, Any> {
        require(file.isFile) { "missing_file: ${file.path}" }
        return read(file.name, file.readText(), supportedSchemaVersion)
    }

    fun read(fileName: String, text: String, supportedSchemaVersion: Int): Map<String, Any> {
        val document = try {
            YamlCodec.DOCUMENT.load(text)
        } catch (failure: YAMLException) {
            throw IllegalArgumentException("unreadable_yaml: $fileName: ${failure.message}", failure)
        }
        SchemaVersion.require(document, supportedSchemaVersion, fileName)
        return document
    }

    fun write(file: File, document: Any): File = writeText(file, YamlCodec.DOCUMENT.dump(document))

    // a file rewritten as each case finishes is never left half written by a process that dies
    fun writeText(file: File, text: String): File = AtomicFile.write(file, text)
}
