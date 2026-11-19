package io.github.junekim0007.cryptobench.preparation.peer

import io.github.junekim0007.cryptobench.preparation.key.generate.KeyMaterial
import io.github.junekim0007.cryptobench.preparation.key.plan.KeyRecipe
import io.github.junekim0007.cryptobench.preparation.measurement.BenchmarkCase
import io.github.junekim0007.cryptobench.preparation.operation.Invocations
import io.github.junekim0007.cryptobench.preparation.operation.OperationDefinitions
import io.github.junekim0007.cryptobench.preparation.prepare.PreparedCase

/** A call a consumer judges: the case as prepared, the engine it read back and what it returned. */
class ProducedCall(val prepared: PreparedCase, val engine: Any?, val output: Any?) {

    companion object {

        // the producer's own call, once, at each side's defaults: its input built, its engine read back
        fun of(case: BenchmarkCase, recipe: KeyRecipe, key: KeyMaterial): ProducedCall {
            val prepared = PreparedCase(case, recipe, key, null, null, OperationDefinitions.of(case.operation).input(case, key, null))
            val invocation = Invocations.of(prepared)
            val output = invocation.once()
            return ProducedCall(prepared, invocation.engine, output)
        }
    }
}
