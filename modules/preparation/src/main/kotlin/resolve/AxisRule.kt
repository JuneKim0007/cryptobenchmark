package io.github.junekim0007.cryptobench.preparation.resolve

import io.github.junekim0007.cryptobench.preparation.measurement.Operation

data class AxisRule(
    val usesKeySize: Boolean,
    val usesInputSize: Boolean,
    val operations: List<Operation>,
) {

    init {
        require(operations.isNotEmpty()) { "missing_field: operations" }
    }
}
