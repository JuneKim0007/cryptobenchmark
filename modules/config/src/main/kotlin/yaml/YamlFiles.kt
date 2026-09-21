package io.github.junekim0007.cryptobench.config.yaml

import java.io.File

class YamlFiles(private val codec: YamlCodec = YamlCodec()) {

    fun <T> at(file: File, handler: DocumentHandler<T>): YamlFile<T> = YamlFile(file, handler, codec)

    fun <T> readOnly(file: File, reader: DocumentReader<T>): ReadOnlyYamlFile<T> = ReadOnlyYamlFile(file, reader, codec)
}
