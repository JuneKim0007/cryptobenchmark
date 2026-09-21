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
import io.github.junekim0007.cryptobench.preparation.global.OnFailure
import io.github.junekim0007.cryptobench.preparation.report.SkipFile
import io.github.junekim0007.cryptobench.preparation.resolve.CaseResolver
import io.github.junekim0007.cryptobench.preparation.global.GlobalReader
import io.github.junekim0007.cryptobench.preparation.inbound.InboundFile
import io.github.junekim0007.cryptobench.preparation.primitive.PrimitiveReader
import io.github.junekim0007.cryptobench.preparation.request.BenchmarkRequest
import java.io.File

class Preparation(
    capability: DeviceCapability,
    private val report: SkipFile,
    private val resolver: CaseResolver = CaseResolver(capability),
    private val planner: KeyPlanner = KeyPlanner(capability),
    private val generator: KeyMaterialGenerator = KeyMaterialGenerator(),
    private val binder: ParameterBinder = ParameterBinder(),
) {

    fun prepare(effectiveFile: File): PreparedRun {
        val inbound = InboundFile.read(effectiveFile)
        val global = GlobalReader.read(inbound)
        val request = BenchmarkRequest(PrimitiveReader.read(inbound, global), global)
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
        if (skipped.isNotEmpty() && global.onFailure == OnFailure.STOP) {
            throw StoppedOnFailureException(skipped)
        }
        require(prepared.isNotEmpty()) { "nothing_prepared: every case was skipped, see ${report.file}" }
        return PreparedRun(prepared, skipped, global.processRepetitions)
    }

    private fun bound(case: BenchmarkCase) =
        if (case.parameters.isEmpty()) null else binder.bind(case.parameters, "parameters")

    private fun skip(case: BenchmarkCase, reason: String) =
        Skip(Skip.PREPARATION, case.provider, case.type, case.algorithm, "${case.id}: $reason")
}
