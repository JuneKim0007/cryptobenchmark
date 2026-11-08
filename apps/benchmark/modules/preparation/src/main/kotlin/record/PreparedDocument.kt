package io.github.junekim0007.cryptobench.preparation.record

import io.github.junekim0007.cryptobench.settings.HarnessSettings
import io.github.junekim0007.cryptobench.preparation.input.OperationInput
import io.github.junekim0007.cryptobench.preparation.key.generate.KeyMaterial
import io.github.junekim0007.cryptobench.preparation.key.plan.KeyRecipe
import io.github.junekim0007.cryptobench.preparation.parameter.resolve.Fingerprint
import io.github.junekim0007.cryptobench.preparation.prepare.PreparedCase
import io.github.junekim0007.cryptobench.preparation.measurement.BenchmarkCase
import io.github.junekim0007.cryptobench.preparation.prepare.Listing
import io.github.junekim0007.cryptobench.preparation.shared.YamlCodec

internal object PreparedDocument {

    const val SCHEMA_VERSION = 2
    const val RESOLVED_PARAMETERS = "resolvedParameters"

    // A listed case stands for itself until its process replaces it with the prepared entry or removes it.
    fun of(listing: Listing, cases: List<BenchmarkCase>): Map<String, Any> = linkedMapOf(
        "schemaVersion" to SCHEMA_VERSION,
        "generatedFrom" to linkedMapOf<String, Any>("effective" to listing.effectiveFileName).apply { listing.runId?.let { put("runId", it) } },
        "run" to linkedMapOf<String, Any>(
            "seed" to listing.global.seed,
            "processRepetitions" to listing.global.processRepetitions,
        ).apply { harnessOf(listing.global.harness)?.let { put("harness", it) } },
        "cases" to cases.map(::listed),
    )

    fun listed(case: BenchmarkCase): Map<String, Any> = LinkedHashMap<String, Any>().apply {
        put("id", case.id)
        put("type", case.type)
        put("algorithm", case.algorithm)
        put("provider", case.provider)
        put("operation", case.operation.name)
        if (case.group.isNotEmpty()) put("group", case.group)
        case.keySize?.let { put("keySize", it) }
        case.inputSize?.let { put("inputSize", it) }
        put("phase", case.phase.name)
        put("variant", case.variant.label)
        put("metrics", case.metrics.map { it.name })
        harnessOf(case.harness)?.let { put("harness", it) }
    }

    fun case(prepared: PreparedCase): Map<String, Any> {
        val described = described(prepared)
        return LinkedHashMap(described).apply {
            put("fingerprint", Fingerprint.of(YamlCodec().dump(described)))
            prepared.perCall?.let { put("perCall", it.label) }
            put(RESOLVED_PARAMETERS, LinkedHashMap(prepared.resolvedParameters))
        }
    }

    // The listed fields with the chart group before the sizes, then what preparation made: the fingerprint's input, in today's order.
    private fun described(prepared: PreparedCase): Map<String, Any> {
        val case = prepared.case
        return LinkedHashMap<String, Any>().apply {
            for ((name, value) in listed(case)) {
                if (name in AFTER_CHART_GROUP && "chartGroup" !in this) {
                    put("chartGroup", prepared.chartGroup.label)
                    put("chartGroupId", prepared.chartGroup.id)
                }
                put(name, value)
            }
            put("key", key(prepared.recipe, prepared.key))
            if (case.keyParameters.isNotEmpty()) put("keyParameters", LinkedHashMap(case.keyParameters))
            if (case.parameters.isNotEmpty()) put("parameters", LinkedHashMap(case.parameters))
            if (prepared.parameters?.varies == true) put("specPerIteration", true)
            put("input", input(prepared.input))
        }
    }

    private val AFTER_CHART_GROUP = setOf("keySize", "inputSize", "phase")

    private fun key(recipe: KeyRecipe, material: KeyMaterial): Map<String, Any> = when (recipe) {
        is KeyRecipe.None -> linkedMapOf("kind" to recipe.kind)
        is KeyRecipe.Secret -> linkedMapOf<String, Any>("kind" to recipe.kind, "algorithm" to recipe.algorithm, "provider" to recipe.provider).apply {
            recipe.keySize?.let { put("keySize", it) }
            if (recipe.parameters.isNotEmpty()) put("parameters", LinkedHashMap(recipe.parameters))
            put("encodedBytes", material.secretKeyOrNull?.encoded?.size ?: 0)
        }
        is KeyRecipe.Pair -> linkedMapOf<String, Any>("kind" to recipe.kind, "algorithm" to recipe.algorithm, "provider" to recipe.provider).apply {
            recipe.keySize?.let { put("keySize", it) }
            if (recipe.parameters.isNotEmpty()) put("parameters", LinkedHashMap(recipe.parameters))
            put("pairs", material.keyPairsOrNull?.size ?: 0)
        }
        is KeyRecipe.Unavailable -> linkedMapOf("kind" to recipe.kind, "reason" to recipe.reason)
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

    private fun harnessOf(harness: HarnessSettings): Map<String, Any>? = HarnessSettings.write(harness).takeIf { it.isNotEmpty() }
}
