package io.github.junekim0007.cryptobench.preparation.prepare

import io.github.junekim0007.cryptobench.preparation.input.OperationInput
import io.github.junekim0007.cryptobench.preparation.key.generate.KeyMaterial
import io.github.junekim0007.cryptobench.preparation.key.plan.KeyRecipe
import io.github.junekim0007.cryptobench.preparation.measurement.BenchmarkCase
import io.github.junekim0007.cryptobench.preparation.parameter.bind.BoundParameters

data class PreparedCase(
    val case: BenchmarkCase,
    val recipe: KeyRecipe,
    val key: KeyMaterial,
    val parameters: BoundParameters?,
    val keyParameters: BoundParameters?,
    val input: OperationInput,
)
