package io.github.junekim0007.cryptobench.preparation

import io.github.junekim0007.cryptobench.preparation.engine.EngineTypes
import io.github.junekim0007.cryptobench.preparation.key.generate.KeyMaterial
import io.github.junekim0007.cryptobench.preparation.key.generate.KeyMaterialGenerator
import io.github.junekim0007.cryptobench.preparation.key.plan.KeyPlanner
import io.github.junekim0007.cryptobench.preparation.key.plan.KeyRecipe
import io.github.junekim0007.cryptobench.preparation.measurement.BenchmarkCase
import io.github.junekim0007.cryptobench.preparation.operation.OperationDefinitions
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
    engineTypes: EngineTypes = EngineTypes.standard(),
    private val resolver: CaseResolver = CaseResolver(capability, engineTypes),
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
            val material = key.getOrElse { failure ->
                skipped += skip(case, "key_generation_failed: ${failure.message}")
                continue
            }
            val parameters = bound(case)
            val definition = OperationDefinitions.of(case.operation)
            val input = runCatching { definition.input(case, material, parameters) }.getOrElse { failure ->
                skipped += skip(case, "input_preparation_failed: ${failure.javaClass.simpleName}: ${failure.message}")
                continue
            }
            val candidate = PreparedCase(case, recipe, material, parameters, input)
            val failure = runCatching { definition.check(candidate) }.exceptionOrNull()
            if (failure != null) {
                skipped += skip(case, "dry_run_failed: ${failure.javaClass.simpleName}: ${failure.message}")
                continue
            }
            prepared += candidate
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
