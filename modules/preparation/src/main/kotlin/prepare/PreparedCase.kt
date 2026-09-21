package io.github.junekim0007.cryptobench.preparation.prepare

import io.github.junekim0007.cryptobench.preparation.key.generate.KeyMaterial
import io.github.junekim0007.cryptobench.preparation.key.plan.KeyRecipe
import io.github.junekim0007.cryptobench.preparation.measurement.BenchmarkCase
import io.github.junekim0007.cryptobench.preparation.parameter.bind.BoundParameters

/** Everything one measurement needs, made before the timer: the case, its key, its bound operation parameters. */
data class PreparedCase(
    val case: BenchmarkCase,
    val recipe: KeyRecipe,
    val key: KeyMaterial,
    /** Null when the provider fills the parameters in. When `varies`, the harness takes a pool of `next()` before timing. */
    val parameters: BoundParameters?,
)
