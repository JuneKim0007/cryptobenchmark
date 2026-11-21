package io.github.junekim0007.cryptobench.document.versioned

interface DocumentHandler<T> : DocumentReader<T> {

    fun of(value: T): Map<String, Any>
}
