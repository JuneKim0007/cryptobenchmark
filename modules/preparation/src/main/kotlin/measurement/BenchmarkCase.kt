package io.github.junekim0007.cryptobench.preparation.measurement

data class BenchmarkCase(
    val type: String,
    val algorithm: String,
    val provider: String,
    val keySize: Int? = null,
    val inputSize: Int? = null,
    val phase: Phase = Phase.WARM,
    val metrics: Set<Metric> = setOf(Metric.TIME),
    val seed: Long = 0L,
    val keyParameters: Map<String, Any> = emptyMap(),
    val parameters: Map<String, Any> = emptyMap(),
) {

    init {
        require(type.isNotBlank()) { "missing_field: type" }
        require(algorithm.isNotBlank()) { "missing_field: algorithm" }
        require(provider.isNotBlank()) { "missing_field: provider" }
        require(keySize == null || keySize > 0) { "not_positive: keySize $keySize" }
        require(inputSize == null || inputSize > 0) { "not_positive: inputSize $inputSize" }
        require(metrics.isNotEmpty()) { "missing_field: metrics" }
    }

    val id: String get() = CaseName.of(this)

    override fun toString(): String = id
}
