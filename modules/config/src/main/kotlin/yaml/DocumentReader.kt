package io.github.junekim0007.cryptobench.config.yaml

/** Map → value for one kind of YAML file. `schemaVersion` is checked by the file before `parse` is called. */
interface DocumentReader<T> {

    val schemaVersion: Int

    fun parse(document: Map<String, Any>): T
}
