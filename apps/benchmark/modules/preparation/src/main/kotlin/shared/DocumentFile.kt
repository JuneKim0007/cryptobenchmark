package io.github.junekim0007.cryptobench.preparation.shared

import org.yaml.snakeyaml.error.YAMLException
import java.io.File
import java.io.IOException

internal object DocumentFile {

    fun read(file: File, schemaName: String, supportedSchemaVersion: Int): Map<String, Any> {
        require(file.isFile) { "missing_file: ${file.path}" }
        return read(file.name, file.readText(), schemaName, supportedSchemaVersion)
    }

    fun read(fileName: String, text: String, schemaName: String, supportedSchemaVersion: Int): Map<String, Any> {
        val document = try {
            YamlCodec().load(text)
        } catch (failure: YAMLException) {
            throw IllegalArgumentException("unreadable_yaml: $fileName: ${failure.message}", failure)
        }
        val schemaVersion = DocumentFields.number(document, "schemaVersion").toInt()
        require(schemaVersion == supportedSchemaVersion) {
            "unsupported_${schemaName}_schema: $fileName: $schemaVersion, this build reads $supportedSchemaVersion"
        }
        return document
    }

    fun write(file: File, document: Any): File {
        val directory = file.parentFile
        if (!directory.exists() && !directory.mkdirs()) {
            throw IOException("cannot create ${directory.absolutePath}")
        }
        file.writeText(YamlCodec().dump(document), Charsets.UTF_8)
        return file
    }
}
