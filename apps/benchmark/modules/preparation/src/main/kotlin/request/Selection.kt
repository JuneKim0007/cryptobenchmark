package io.github.junekim0007.cryptobench.preparation.request

import io.github.junekim0007.cryptobench.preparation.key.plan.KeySource
import io.github.junekim0007.cryptobench.preparation.measurement.Variant
import io.github.junekim0007.cryptobench.settings.HarnessSettings
import io.github.junekim0007.cryptobench.preparation.measurement.Operation

data class Selection(
    val type: String,
    val algorithm: String,
    val provider: String,
    val keySizes: List<Int> = emptyList(),
    val inputSizes: List<Int> = emptyList(),
    val keyParameters: Map<String, Any> = emptyMap(),
    val keySource: KeySource = KeySource(),
    val parameters: Map<String, Any> = emptyMap(),
    val operations: Set<Operation> = emptySet(),
    val group: String = "",
    val harness: HarnessSettings = HarnessSettings(),
    // null: the run's
    val variants: List<Variant>? = null,
) {

    init {
        require(type.isNotBlank()) { "missing_field: type" }
        require(algorithm.isNotBlank()) { "missing_field: algorithm" }
        require(!group.contains('@')) { "invalid_group: $group" }
        require(provider.isNotBlank()) { "blank_provider: $type/$algorithm" }
        require(keySizes.all { it > 0 }) { "not_positive: keySizes $keySizes" }
        require(keySizes.size == keySizes.distinct().size) { "duplicate: keySizes $keySizes" }
        require(inputSizes.all { it > 0 }) { "not_positive: inputSizes $inputSizes" }
        require(inputSizes.size == inputSizes.distinct().size) { "duplicate: inputSizes $inputSizes" }
        require(variants == null || variants.size == variants.distinct().size) { "duplicate: variants $variants" }
    }
}
