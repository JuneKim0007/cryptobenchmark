package io.github.junekim0007.cryptobench.discovery.query

/** One algorithm across every provider that registers it: declared modes and paddings, in declaration order. */
data class ServiceShape(
    val modes: List<String>,
    val paddings: List<String>,
    val providers: List<String>,
)
