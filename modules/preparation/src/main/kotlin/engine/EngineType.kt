package io.github.junekim0007.cryptobench.preparation.engine

import io.github.junekim0007.cryptobench.preparation.global.GlobalSettings
import io.github.junekim0007.cryptobench.preparation.measurement.Operation
import io.github.junekim0007.cryptobench.preparation.request.Selection

data class EngineType(
    val operations: List<Operation>,
    val usesKeySize: Boolean,
    val usesInputSize: Boolean,
    val keyShape: KeyShape,
) {

    init {
        require(operations.isNotEmpty()) { "missing_field: operations" }
    }

    fun operationsFor(selection: Selection): List<Operation> = selection.operations.ifEmpty { operations }.toList()

    fun keySizesFor(selection: Selection): List<Int?> =
        if (usesKeySize && selection.keySizes.isNotEmpty()) selection.keySizes else listOf(null)

    fun inputSizesFor(selection: Selection, global: GlobalSettings): List<Int?> =
        if (usesInputSize) global.inputSizesFor(selection.inputSizes) else listOf(null)
}
