package io.github.junekim0007.cryptobench.preparation.prepare

import io.github.junekim0007.cryptobench.preparation.key.generate.KeyMaterial
import io.github.junekim0007.cryptobench.preparation.key.generate.KeyMaterialGenerator
import io.github.junekim0007.cryptobench.preparation.key.plan.KeyPlanner
import io.github.junekim0007.cryptobench.preparation.key.plan.KeyRecipe
import io.github.junekim0007.cryptobench.preparation.measurement.BenchmarkCase
import io.github.junekim0007.cryptobench.preparation.operation.OperationDefinitions
import io.github.junekim0007.cryptobench.preparation.parameter.bind.ParameterBinder
import io.github.junekim0007.cryptobench.preparation.parameter.resolve.ResolvedParameters
import io.github.junekim0007.cryptobench.preparation.report.Skip
import io.github.junekim0007.cryptobench.preparation.shared.Attempt
import io.github.junekim0007.cryptobench.preparation.shared.FailureText

/**
 * Builds one case: plan its key, make it (once per recipe), bind its parameters, build its input, call it once, read back what the provider used.
 * A case that cannot be built is a [Skip] with the reason, never an exception: whether that stops the run is the caller's policy.
 * One instance per run, because the keys it made are reused by every case with the same recipe.
 */
internal class CasePreparer(
    private val planner: KeyPlanner,
    private val generator: KeyMaterialGenerator,
    private val binder: ParameterBinder,
) {

    sealed interface Outcome {
        class Prepared(val case: PreparedCase) : Outcome
        class Skipped(val skip: Skip) : Outcome
    }

    private val keys = HashMap<KeyRecipe, Result<KeyMaterial>>()

    fun prepare(case: BenchmarkCase): Outcome {
        val recipe = planner.plan(case)
        if (recipe is KeyRecipe.Unavailable) return skipped(case, recipe.reason)
        val material = keys.getOrPut(recipe) { Attempt.of { generator.generate(recipe) } }
            .getOrElse { failure -> return skipped(case, FailureText.of(failure, "key_generation_failed: ")) }
        val definition = OperationDefinitions.of(case.operation)
        val parameters = bound(case.parameters, "parameters")
        val keyParameters = if (recipe is KeyRecipe.None) bound(case.keyParameters, "key") else null
        val input = Attempt.of { definition.input(case, material, parameters) }
            .getOrElse { failure -> return skipped(case, FailureText.of(failure, "input_preparation_failed: ")) }
        val candidate = PreparedCase(case, recipe, material, parameters, keyParameters, input)
        val invocation = Attempt.of { definition.invocation(candidate) }
            .getOrElse { failure -> return skipped(case, FailureText.of(failure, "dry_run_failed: ")) }
        val result = Attempt.of { invocation.once() }
            .getOrElse { failure -> return skipped(case, FailureText.of(failure, "dry_run_failed: ")) }
        val resolved = Attempt.of { ResolvedParameters.of(invocation.engine, material, result) }
            .getOrElse { failure -> return skipped(case, FailureText.of(failure, "parameters_unreadable: ")) }
        return Outcome.Prepared(candidate.copy(resolvedParameters = resolved, perCall = invocation.perCall))
    }

    private fun bound(tree: Map<String, Any>, path: String) =
        if (tree.isEmpty()) null else binder.bind(tree, path)

    private fun skipped(case: BenchmarkCase, reason: String) =
        Outcome.Skipped(Skip(Skip.PREPARATION, case.provider, case.type, case.algorithm, "${case.id}: $reason"))
}
