package io.github.junekim0007.cryptobench.preparation.prepare

import io.github.junekim0007.cryptobench.preparation.key.generate.KeyMaterial
import io.github.junekim0007.cryptobench.preparation.key.generate.KeyMaterialGenerator
import io.github.junekim0007.cryptobench.preparation.key.plan.KeyPlanner
import io.github.junekim0007.cryptobench.preparation.key.plan.KeyRecipe
import io.github.junekim0007.cryptobench.preparation.input.OperationInput
import io.github.junekim0007.cryptobench.preparation.key.secure.KeyInfoFields
import io.github.junekim0007.cryptobench.preparation.key.secure.SecureKey
import io.github.junekim0007.cryptobench.preparation.measurement.BenchmarkCase
import io.github.junekim0007.cryptobench.preparation.measurement.KeySource
import io.github.junekim0007.cryptobench.preparation.measurement.Variant
import io.github.junekim0007.cryptobench.jca.bind.BoundParameters
import io.github.junekim0007.cryptobench.preparation.operation.Invocations
import io.github.junekim0007.cryptobench.preparation.operation.OperationDefinitions
import io.github.junekim0007.cryptobench.jca.bind.ParameterBinder
import io.github.junekim0007.cryptobench.preparation.parameter.resolve.ResolvedParameters
import io.github.junekim0007.cryptobench.jca.failure.Attempt
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
    private val sdkInt: Int? = null,
    private val platform: String? = null,
) {

    private val keys = HashMap<KeyRecipe, Result<KeyMaterial>>()

    fun prepare(case: BenchmarkCase): PreparedCase {
        val recipe = planner.plan(case)
        if (recipe is KeyRecipe.Unavailable) throw PreparationException(recipe.reason)
        val material = step("key_generation_failed: ") { keys.getOrPut(recipe) { Attempt.of { generator.generate(recipe) } }.getOrThrow() }
        val definition = OperationDefinitions.of(case.operation)
        val parameters = bound(case.parameters, "parameters")
        val keyParameters = if (recipe is KeyRecipe.None) bound(case.keyParameters, "key") else null
        if (case.variant == Variant.SECURE) return secure(case, recipe, material, keyParameters)
        val input = step("input_preparation_failed: ") { definition.input(case, material, parameters) }
        val candidate = PreparedCase(case, recipe, material, parameters, keyParameters, input, platform = platform)
        val invocation = step("dry_run_failed: ") { Invocations.of(candidate) }
        val result = step("dry_run_failed: ") { invocation.once() }
        step("parameters_unreadable: ") { definition.parametersIgnored(case, material, parameters) }?.let { throw PreparationException(it) }
        val resolved = step("parameters_unreadable: ") { ResolvedParameters.of(invocation.engine, material, result) }
        return candidate.copy(resolvedParameters = resolved, perCall = invocation.perCall)
    }

    // a key born inside its provider: the spec carries the slot's alias; the dry run's key is read back, then the slot emptied
    private fun secure(case: BenchmarkCase, recipe: KeyRecipe, material: KeyMaterial, keyParameters: BoundParameters?): PreparedCase {
        val key = SecureKey(case, sdkInt)
        val spec = step(key::refusal) { BoundParameters.cycling(listOf(key.spec(keyParameters?.next()))) }
        val candidate = PreparedCase(case, recipe, material, null, spec, OperationInput.None, platform = platform, afterCall = key::delete)
        val invocation = step(key::refusal) { Invocations.of(candidate) }
        val result = step(key::refusal) { invocation.once() }
        // the slot is emptied whatever happens; a failed delete is suppressed under the read's failure, never in its place
        return AutoCloseable { step(key::refusal) { key.delete() } }.use {
            val observed = step("parameters_unreadable: ") { KeyInfoFields.of(result, case.provider) }
            val resolved = step("parameters_unreadable: ") { ResolvedParameters.of(invocation.engine, material, result) }
            val levels = linkedMapOf<String, Any>(KeySource.BACKING to case.keySource.requestedBacking, KeyInfoFields.SECURITY_LEVEL to observed.getValue(KeyInfoFields.SECURITY_LEVEL))
            candidate.copy(resolvedParameters = observed.filterKeys { it == KeyInfoFields.KEY_BITS } + resolved + levels, perCall = invocation.perCall)
        }
    }

    private inline fun <T> step(code: String, block: () -> T): T = step({ FailureText.of(it, code) }, block)

    private inline fun <T> step(reason: (Throwable) -> String, block: () -> T): T =
        Attempt.of(block).getOrElse { failure -> throw PreparationException(reason(failure), failure) }

    private fun bound(tree: Map<String, Any>, path: String) =
        if (tree.isEmpty()) null else binder.bind(tree, path)
}
