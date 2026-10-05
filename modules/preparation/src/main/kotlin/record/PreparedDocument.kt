package io.github.junekim0007.cryptobench.preparation.record

import io.github.junekim0007.cryptobench.preparation.global.HarnessSettings
import io.github.junekim0007.cryptobench.preparation.input.OperationInput
import io.github.junekim0007.cryptobench.preparation.key.generate.KeyMaterial
import io.github.junekim0007.cryptobench.preparation.key.plan.KeyRecipe
import io.github.junekim0007.cryptobench.preparation.prepare.PreparedCase
import io.github.junekim0007.cryptobench.preparation.prepare.PreparedRun
import io.github.junekim0007.cryptobench.preparation.shared.YamlCodec

internal object PreparedDocument {

    const val SCHEMA_VERSION = 1

    fun of(run: PreparedRun, effectiveFileName: String, harness: HarnessSettings, seed: Long): Map<String, Any> = linkedMapOf(
        "schemaVersion" to SCHEMA_VERSION,
        "generatedFrom" to linkedMapOf("effective" to effectiveFileName),
        "run" to linkedMapOf<String, Any>(
            "seed" to seed,
            "processRepetitions" to run.processRepetitions,
        ).apply { harnessOf(harness)?.let { put("harness", it) } },
        "cases" to run.cases.map { prepared -> case(prepared) },
    )

    private fun case(prepared: PreparedCase): Map<String, Any> {
        val described = described(prepared)
        return LinkedHashMap(described).apply { put("fingerprint", Fingerprint.of(YamlCodec().dump(described))) }
    }

    private fun described(prepared: PreparedCase): Map<String, Any> {
        val case = prepared.case
        return LinkedHashMap<String, Any>().apply {
            put("id", case.id)
            put("type", case.type)
            put("algorithm", case.algorithm)
            put("provider", case.provider)
            put("operation", case.operation.name)
            if (case.group.isNotEmpty()) put("group", case.group)
            put("chartGroup", case.chartGroup.label)
            put("chartGroupId", case.chartGroup.id)
            case.keySize?.let { put("keySize", it) }
            case.inputSize?.let { put("inputSize", it) }
            put("phase", case.phase.name)
            put("metrics", case.metrics.map { it.name })
            harnessOf(case.harness)?.let { put("harness", it) }
            put("key", key(prepared.recipe, prepared.key))
            if (case.keyParameters.isNotEmpty()) put("keyParameters", LinkedHashMap(case.keyParameters))
            if (case.parameters.isNotEmpty()) put("parameters", LinkedHashMap(case.parameters))
            if (prepared.parameters?.varies == true) put("specPerIteration", true)
            put("input", input(prepared.input))
        }
    }

    private fun key(recipe: KeyRecipe, material: KeyMaterial): Map<String, Any> = when (recipe) {
        is KeyRecipe.None -> linkedMapOf("kind" to "none")
        is KeyRecipe.Secret -> linkedMapOf<String, Any>("kind" to "secret", "algorithm" to recipe.algorithm, "provider" to recipe.provider).apply {
            recipe.keySize?.let { put("keySize", it) }
            if (recipe.parameters.isNotEmpty()) put("parameters", LinkedHashMap(recipe.parameters))
            put("encodedBytes", material.secretKeyOrNull?.encoded?.size ?: 0)
        }
        is KeyRecipe.Pair -> linkedMapOf<String, Any>("kind" to "pair", "algorithm" to recipe.algorithm, "provider" to recipe.provider).apply {
            recipe.keySize?.let { put("keySize", it) }
            if (recipe.parameters.isNotEmpty()) put("parameters", LinkedHashMap(recipe.parameters))
            put("pairs", material.keyPairsOrNull?.size ?: 0)
        }
        is KeyRecipe.Unavailable -> linkedMapOf("kind" to "unavailable", "reason" to recipe.reason)
    }

    private fun input(input: OperationInput): Map<String, Any> = when (input) {
        is OperationInput.None -> linkedMapOf("kind" to "none")
        is OperationInput.Message -> linkedMapOf("kind" to "message", "bytes" to input.bytes.size)
        is OperationInput.SignedMessage -> linkedMapOf("kind" to "signedMessage", "bytes" to input.message.size)
        is OperationInput.Ciphertext -> linkedMapOf(
            "kind" to "ciphertext",
            "bytes" to input.bytes.size,
            "plaintextBytes" to input.plaintextSize,
            "spec" to when {
                input.spec != null -> "carried"
                input.providerParameters != null -> "provider"
                else -> "none"
            },
        )
    }

    private fun harnessOf(harness: HarnessSettings): Map<String, Any>? = LinkedHashMap<String, Any>().apply {
        harness.iterations?.let { put("iterations", it) }
        harness.warmupIterations?.let { put("warmupIterations", it) }
        harness.profiling?.let { put("profiling", it) }
    }.takeIf { it.isNotEmpty() }
}
