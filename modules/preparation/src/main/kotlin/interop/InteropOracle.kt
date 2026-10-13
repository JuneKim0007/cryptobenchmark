package io.github.junekim0007.cryptobench.preparation.interop

import io.github.junekim0007.cryptobench.preparation.engine.EngineTypes
import io.github.junekim0007.cryptobench.preparation.interop.check.CrossCheck
import io.github.junekim0007.cryptobench.preparation.interop.check.PairCases
import io.github.junekim0007.cryptobench.preparation.interop.plan.InteropPair
import io.github.junekim0007.cryptobench.preparation.interop.plan.Member
import io.github.junekim0007.cryptobench.preparation.interop.report.InteropVerdict
import io.github.junekim0007.cryptobench.preparation.interop.report.Outcome
import io.github.junekim0007.cryptobench.preparation.key.generate.KeyMaterialGenerator
import io.github.junekim0007.cryptobench.preparation.key.plan.KeyPlanner
import io.github.junekim0007.cryptobench.preparation.key.plan.KeyRecipe
import io.github.junekim0007.cryptobench.preparation.measurement.Operation
import io.github.junekim0007.cryptobench.preparation.operation.OperationDefinitions
import io.github.junekim0007.cryptobench.preparation.port.Availability
import io.github.junekim0007.cryptobench.preparation.port.DeviceCapability

class InteropOracle(
    private val capability: DeviceCapability,
    private val engineTypes: EngineTypes = EngineTypes.standard(),
    private val planner: KeyPlanner = KeyPlanner(capability),
    private val generator: KeyMaterialGenerator = KeyMaterialGenerator(),
) {

    fun check(pair: InteropPair): InteropVerdict {
        val missing = listOf(pair.a, pair.b).mapNotNull { m ->
            (capability.check(m.provider, m.type, m.algorithm) as? Availability.Unavailable)?.let { "$m: ${it.reason}" }
        }
        if (missing.isNotEmpty()) {
            val out = Outcome.Untestable("not_registered: ${missing.joinToString()}")
            return InteropVerdict(pair.id, InteropVerdict.NONE, out, out)
        }
        val operations = engineTypes.operationsOf(pair.a.type)
        val consuming = operations.firstOrNull { OperationDefinitions.of(it).consumesArtifact }
        val operation = consuming ?: operations.first()
        val mode = if (consuming != null) InteropVerdict.PRODUCE_CONSUME else InteropVerdict.SAME_OUTPUT
        return InteropVerdict(pair.id, mode, direction(pair.a, pair.b, operation, pair, consuming != null),
                              direction(pair.b, pair.a, operation, pair, consuming != null))
    }

    private fun direction(first: Member, second: Member, operation: Operation, pair: InteropPair, produce: Boolean): Outcome {
        val one = PairCases.of(first, operation, pair)
        val other = PairCases.of(second, operation, pair)
        val recipe = planner.plan(one)
        if (recipe is KeyRecipe.Unavailable) return Outcome.Untestable("no_key: ${recipe.reason}")
        val key = try {
            generator.generate(recipe)
        } catch (failure: Exception) {
            return Outcome.Untestable("key_generation_failed: ${failure.javaClass.simpleName}: ${failure.message}")
        }
        return if (produce) CrossCheck.produceConsume(one, other, recipe, key) else CrossCheck.sameOutput(one, other, recipe, key)
    }
}
