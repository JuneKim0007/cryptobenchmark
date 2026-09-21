package io.github.junekim0007.cryptobench.preparation

import io.github.junekim0007.cryptobench.preparation.key.generate.KeyMaterial
import io.github.junekim0007.cryptobench.preparation.key.generate.KeyMaterialGenerator
import io.github.junekim0007.cryptobench.preparation.key.plan.KeyPlanner
import io.github.junekim0007.cryptobench.preparation.key.plan.KeyRecipe
import io.github.junekim0007.cryptobench.preparation.measurement.BenchmarkCase
import io.github.junekim0007.cryptobench.preparation.parameter.bind.ParameterBinder
import io.github.junekim0007.cryptobench.preparation.port.DeviceCapability
import io.github.junekim0007.cryptobench.preparation.prepare.PreparedCase
import io.github.junekim0007.cryptobench.preparation.prepare.PreparedRun
import io.github.junekim0007.cryptobench.preparation.prepare.StoppedOnFailureException
import io.github.junekim0007.cryptobench.preparation.report.Skip
import io.github.junekim0007.cryptobench.preparation.request.OnFailure
import io.github.junekim0007.cryptobench.preparation.report.SkipFile
import io.github.junekim0007.cryptobench.preparation.resolve.CaseResolver
import io.github.junekim0007.cryptobench.preparation.source.ConfigSource
import java.io.File

/**
 * The module's entry point: effective.yaml → prepared cases. Every failure this stage can see — a rejected selection,
 * a key that cannot be planned or generated — is either recorded and skipped or stops the run, as the policy says.
 */
class Preparation(
    capability: DeviceCapability,
    private val report: SkipFile,
    private val source: ConfigSource = ConfigSource(),
    private val resolver: CaseResolver = CaseResolver(capability),
    private val planner: KeyPlanner = KeyPlanner(capability),
    private val generator: KeyMaterialGenerator = KeyMaterialGenerator(),
    private val binder: ParameterBinder = ParameterBinder(),
) {

    fun prepare(effectiveFile: File): PreparedRun {
        val request = source.read(effectiveFile)
        val resolution = resolver.resolve(request)
        val skipped = resolution.rejections.mapTo(mutableListOf()) { rejection ->
            Skip(Skip.PREPARATION, rejection.provider, rejection.selection.type, rejection.selection.algorithm, rejection.reason)
        }
        val keys = HashMap<KeyRecipe, Result<KeyMaterial>>()
        val prepared = mutableListOf<PreparedCase>()
        for (case in resolution.cases) {
            val recipe = planner.plan(case)
            if (recipe is KeyRecipe.Unavailable) {
                skipped += skip(case, recipe.reason)
                continue
            }
            val key = keys.getOrPut(recipe) { runCatching { generator.generate(recipe) } }
            key.fold(
                onSuccess = { material -> prepared += PreparedCase(case, recipe, material, bound(case)) },
                onFailure = { failure -> skipped += skip(case, "key_generation_failed: ${failure.message}") },
            )
        }
        report.write(skipped)
        if (skipped.isNotEmpty() && request.onFailure == OnFailure.STOP) {
            throw StoppedOnFailureException(skipped)
        }
        require(prepared.isNotEmpty()) { "nothing_prepared: every case was skipped, see ${report.file}" }
        return PreparedRun(prepared, skipped, request.processRepetitions)
    }

    private fun bound(case: BenchmarkCase) =
        if (case.parameters.isEmpty()) null else binder.bind(case.parameters, "parameters")

    private fun skip(case: BenchmarkCase, reason: String) =
        Skip(Skip.PREPARATION, case.provider, case.type, case.algorithm, "${case.id}: $reason")
}
