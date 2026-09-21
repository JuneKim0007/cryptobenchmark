package io.github.junekim0007.cryptobench.benchmark.preparation.resolve

/** Which request axes one engine type is measured along. */
data class AxisRule(
    val usesKeySize: Boolean,
    val usesInputSize: Boolean,
)
