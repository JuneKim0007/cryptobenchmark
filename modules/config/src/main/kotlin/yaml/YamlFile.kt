package io.github.junekim0007.cryptobench.config.yaml

import java.io.File
import java.io.IOException
import java.nio.file.Files
import java.nio.file.StandardOpenOption

class YamlFile<T> internal constructor(
    val file: File,
    private val handler: DocumentHandler<T>,
    private val codec: YamlCodec,
) {

    private val reader = ReadOnlyYamlFile(file, handler, codec)

    fun read(): T = reader.read()

    fun write(value: T): File {
        val directory = file.absoluteFile.parentFile
        if (!directory.exists() && !directory.mkdirs()) {
            throw IOException("cannot create ${directory.absolutePath}")
        }
        val document = linkedMapOf<String, Any>(ReadOnlyYamlFile.SCHEMA_VERSION to handler.schemaVersion)
        document.putAll(handler.of(value))
        Files.write(file.toPath(), codec.dump(document).toByteArray(Charsets.UTF_8),
            StandardOpenOption.CREATE, StandardOpenOption.TRUNCATE_EXISTING, StandardOpenOption.WRITE)
        return file
    }
}
