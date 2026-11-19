package io.github.junekim0007.cryptobench.config.yaml

import io.github.junekim0007.cryptobench.document.AtomicFile
import io.github.junekim0007.cryptobench.document.YamlCodec
import java.io.File

class YamlFile<T> internal constructor(
    val file: File,
    private val handler: DocumentHandler<T>,
    private val codec: YamlCodec,
) {

    private val reader = ReadOnlyYamlFile(file, handler, codec)

    fun read(): T = reader.read()

    fun write(value: T): File {
        val document = linkedMapOf<String, Any>(ReadOnlyYamlFile.SCHEMA_VERSION to handler.schemaVersion)
        document.putAll(handler.of(value))
        return AtomicFile.write(file, codec.dump(document))
    }
}
