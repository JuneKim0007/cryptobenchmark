package io.github.junekim0007.cryptobench.config.yaml

/** Value ⇄ map for one kind of YAML file: the file's schema, in one place. Plumbing is `YamlFile`'s job. */
interface DocumentHandler<T> : DocumentReader<T> {

    fun of(value: T): Map<String, Any>
}
