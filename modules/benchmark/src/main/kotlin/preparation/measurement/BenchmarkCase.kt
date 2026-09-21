package io.github.junekim0007.cryptobench.benchmark.preparation.measurement

/** One measurement, fully named: nothing left to decide or look up once the harness has it. */
data class BenchmarkCase(
    val type: String,
    /** As passed to getInstance: `AES/GCM/NoPadding`, `SHA-256`, `SHA256withRSA`. */
    val algorithm: String,
    val provider: String,
    val keySize: Int? = null,
    /** Bytes per operation; absent for key generation, which takes no input. */
    val inputSize: Int? = null,
    val phase: Phase = Phase.WARM,
    val metrics: Set<Metric> = setOf(Metric.TIME),
    val seed: Long = 0L,
) {

    init {
        require(type.isNotBlank()) { "missing_field: type" }
        require(algorithm.isNotBlank()) { "missing_field: algorithm" }
        require(provider.isNotBlank()) { "missing_field: provider" }
        require(keySize == null || keySize > 0) { "not_positive: keySize $keySize" }
        require(inputSize == null || inputSize > 0) { "not_positive: inputSize $inputSize" }
        require(metrics.isNotEmpty()) { "missing_field: metrics" }
    }

    /** Stable name linking this case to its result: letters, digits and underscores only. */
    val id: String get() = CaseName.of(this)

    override fun toString(): String = id
}
