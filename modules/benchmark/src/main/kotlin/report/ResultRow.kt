package io.github.junekim0007.cryptobench.benchmark.report

class ResultRow(
    val id: String,
    val type: String,
    val algorithm: String,
    val provider: String,
    val operation: String,
    val keySize: Int?,
    val inputSize: Int?,
    // secret|pair|none: separates symmetric from asymmetric, which the JCA engine type cannot (AES and RSA are both Cipher).
    val keyKind: String?,
    metrics: Map<String, MetricSamples>,
) {

    val metrics: Map<String, MetricSamples> = LinkedHashMap(metrics)

    init {
        require(id.isNotBlank()) { "missing_field: id" }
        require(metrics.isNotEmpty()) { "missing_field: metrics" }
        require(metrics.containsKey(MetricSamples.TIME)) { "missing_field: metrics.${MetricSamples.TIME} for $id" }
    }

    val time: MetricSamples? get() = metrics[MetricSamples.TIME]

    fun mergedWith(later: ResultRow): ResultRow {
        require(id == later.id) { "different_case: $id and ${later.id}" }
        val merged = LinkedHashMap(metrics)
        later.metrics.forEach { (metric, samples) ->
            merged[metric] = merged[metric]?.mergedWith(samples) ?: samples
        }
        return ResultRow(id, type, algorithm, provider, operation, keySize, inputSize, keyKind, merged)
    }
}
