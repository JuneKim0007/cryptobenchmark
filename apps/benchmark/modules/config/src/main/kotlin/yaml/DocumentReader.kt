package io.github.junekim0007.cryptobench.config.yaml

interface DocumentReader<T> {

    val schemaVersion: Int

    fun parse(document: Map<String, Any>): T
}
