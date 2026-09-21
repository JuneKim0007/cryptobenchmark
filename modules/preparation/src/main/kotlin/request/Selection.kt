package io.github.junekim0007.cryptobench.preparation.request

data class Selection(
    val type: String,
    val algorithm: String,
    val providers: List<String> = emptyList(),
    val keySizes: List<Int> = emptyList(),
    val inputSizes: List<Int> = emptyList(),
    val keyParameters: Map<String, Any> = emptyMap(),
    val parameters: Map<String, Any> = emptyMap(),
) {

    init {
        require(type.isNotBlank()) { "missing_field: type" }
        require(algorithm.isNotBlank()) { "missing_field: algorithm" }
        require(providers.none { it.isBlank() }) { "blank_provider: $type/$algorithm" }
        require(keySizes.all { it > 0 }) { "not_positive: keySizes $keySizes" }
        require(keySizes.size == keySizes.distinct().size) { "duplicate: keySizes $keySizes" }
        require(inputSizes.all { it > 0 }) { "not_positive: inputSizes $inputSizes" }
        require(inputSizes.size == inputSizes.distinct().size) { "duplicate: inputSizes $inputSizes" }
    }
}
