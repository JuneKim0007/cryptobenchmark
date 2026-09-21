package io.github.junekim0007.cryptobench.discovery.query

data class TransformationFailure(
    val provider: String,
    val algorithm: String,
    val transformation: String,
    val error: String,
)
