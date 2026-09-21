package io.github.junekim0007.cryptobench.config.yaml

import java.io.File

/** Factory: hands every file the same codec, so how YAML is read and written is decided once. */
class YamlFiles(private val codec: YamlCodec = YamlCodec()) {

    fun <T> at(file: File, handler: DocumentHandler<T>): YamlFile<T> = YamlFile(file, handler, codec)

    fun <T> readOnly(file: File, reader: DocumentReader<T>): YamlFile<T> = YamlFile(file, reader, codec)

    /** For text that is not a file, as in tests. */
    fun load(text: String): Map<String, Any> = codec.load(text)

    fun dump(document: Any): String = codec.dump(document)
}
