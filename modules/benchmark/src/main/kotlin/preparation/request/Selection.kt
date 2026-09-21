package io.github.junekim0007.cryptobench.benchmark.preparation.request

/** One primitive the user asked for; providers empty means every provider that serves it. */
data class Selection(
    val type: String,
    /** As passed to getInstance: `AES/GCM/NoPadding`, `SHA-256`, `SHA256withRSA`. */
    val algorithm: String,
    val providers: List<String> = emptyList(),
    val keySizes: List<Int> = emptyList(),
) {

    init {
        require(type.isNotBlank()) { "missing_field: type" }
        require(algorithm.isNotBlank()) { "missing_field: algorithm" }
        require(providers.none { it.isBlank() }) { "blank_provider: $type/$algorithm" }
        require(keySizes.all { it > 0 }) { "not_positive: keySizes $keySizes" }
        require(keySizes.size == keySizes.distinct().size) { "duplicate: keySizes $keySizes" }
    }
}
