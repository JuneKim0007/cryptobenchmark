package io.github.junekim0007.cryptobench.preparation.operation

import io.github.junekim0007.cryptobench.preparation.global.GlobalSettings
import io.github.junekim0007.cryptobench.preparation.input.OperationInput
import io.github.junekim0007.cryptobench.preparation.key.generate.KeyMaterial
import io.github.junekim0007.cryptobench.preparation.measurement.BenchmarkCase
import io.github.junekim0007.cryptobench.preparation.parameter.bind.BoundParameters
import io.github.junekim0007.cryptobench.preparation.prepare.PreparedCase
import io.github.junekim0007.cryptobench.preparation.request.Selection

internal interface OperationDefinition {

    val keyShape: KeyShape

    val consumesKeySize: Boolean

    val consumesInput: Boolean

    fun input(case: BenchmarkCase, key: KeyMaterial, parameters: BoundParameters?): OperationInput

    fun check(prepared: PreparedCase)

    fun keySizesFor(selection: Selection): List<Int?> =
        if (consumesKeySize && selection.keySizes.isNotEmpty()) selection.keySizes else listOf(null)

    fun inputSizesFor(selection: Selection, global: GlobalSettings): List<Int?> =
        if (consumesInput) global.inputSizesFor(selection.inputSizes) else listOf(null)
}
