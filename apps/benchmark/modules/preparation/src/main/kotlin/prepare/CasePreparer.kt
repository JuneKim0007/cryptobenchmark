package io.github.junekim0007.cryptobench.preparation.prepare

import io.github.junekim0007.cryptobench.preparation.key.generate.KeyMaterial
import io.github.junekim0007.cryptobench.preparation.key.generate.KeyMaterialGenerator
import io.github.junekim0007.cryptobench.preparation.key.plan.KeyPlanner
import io.github.junekim0007.cryptobench.preparation.key.plan.KeyRecipe
import io.github.junekim0007.cryptobench.preparation.measurement.BenchmarkCase
import io.github.junekim0007.cryptobench.preparation.operation.OperationDefinitions
import io.github.junekim0007.cryptobench.preparation.parameter.bind.ParameterBinder
import io.github.junekim0007.cryptobench.preparation.parameter.resolve.ResolvedParameters
import io.github.junekim0007.cryptobench.preparation.shared.Attempt
import io.github.junekim0007.cryptobench.preparation.shared.FailureText

/**
 * Builds one case: plan its key, make it (once per recipe), bind its parameters, build its input, call it once, read back what the provider used.
 * A step that fails throws [PreparationException] with the step's code; any other Error escapes as it is. Skipping is the caller's decision.
 * One instance per process, because the keys it made are reused by every case with the same recipe.
 */
internal class CasePreparer(
    private val planner: KeyPlanner,
    private val generator: KeyMaterialGenerator,
    private val binder: ParameterBinder,
) {

    private val keys = HashMap<KeyRecipe, Result<KeyMaterial>>()

    fun prepare(case: BenchmarkCase): PreparedCase {
        val recipe = planner.plan(case)
        if (recipe is KeyRecipe.Unavailable) throw PreparationException(recipe.reason)
        val material = step("key_generation_failed: ") { keys.getOrPut(recipe) { Attempt.of { generator.generate(recipe) } }.getOrThrow() }
        val definition = OperationDefinitions.of(case.operation)
        val parameters = bound(case.parameters, "parameters")
        val keyParameters = if (recipe is KeyRecipe.None) bound(case.keyParameters, "key") else null
        val input = step("input_preparation_failed: ") { definition.input(case, material, parameters) }
        val candidate = PreparedCase(case, recipe, material, parameters, keyParameters, input)
        val invocation = step("dry_run_failed: ") { definition.invocation(candidate) }
        val result = step("dry_run_failed: ") { invocation.once() }
        val resolved = step("parameters_unreadable: ") { ResolvedParameters.of(invocation.engine, material, result) }
        return candidate.copy(resolvedParameters = resolved, perCall = invocation.perCall)
    }

    private inline fun <T> step(code: String, block: () -> T): T =
        Attempt.of(block).getOrElse { failure -> throw PreparationException(FailureText.of(failure, code), failure) }

    private fun bound(tree: Map<String, Any>, path: String) =
        if (tree.isEmpty()) null else binder.bind(tree, path)
}
