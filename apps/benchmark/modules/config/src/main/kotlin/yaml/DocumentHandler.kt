package io.github.junekim0007.cryptobench.config.yaml

interface DocumentHandler<T> : DocumentReader<T> {

    fun of(value: T): Map<String, Any>
}
