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
    // What the provider used: prepared.yaml resolvedParameters.
    val parameters: Map<String, Any>,
    // Jetpack's heat pauses for this case, and the host's temperature reading around it (thermal.json); null when not known.
    val thermalThrottleSleepSeconds: Long? = null,
    val thermal: Map<String, Any?>? = null,
    val thermalNote: String? = null,
    // The host's thermal gate before the case: {waitedSeconds, target, timedOut}; null when no gate ran.
    val gate: Map<String, Any?>? = null,
) {

    val metrics: Map<String, MetricSamples> = LinkedHashMap(metrics)

    init {
        require(id.isNotBlank()) { "missing_field: id" }
        require(metrics.isNotEmpty()) { "missing_field: metrics" }
        require(metrics.containsKey(MetricSamples.TIME)) { "missing_field: metrics.${MetricSamples.TIME} for $id" }
    }

    val time: MetricSamples? get() = metrics[MetricSamples.TIME]

    // Merged processes: the first one's start, the last one's end.
    private fun spanned(first: Map<String, Any?>?, last: Map<String, Any?>?): Map<String, Any?>? = when {
        first == null || last == null -> first ?: last
        else -> LinkedHashMap(first).apply { END_KEYS.forEach { put(it, last[it]) } }
    }

    // Merged processes: every wait added, timed out if any process's gate did, the first target.
    private fun gated(first: Map<String, Any?>?, last: Map<String, Any?>?): Map<String, Any?>? = when {
        first == null || last == null -> first ?: last
        else -> LinkedHashMap(first).apply {
            put(WAITED, seconds(first[WAITED]) + seconds(last[WAITED]))
            put(TIMED_OUT, first[TIMED_OUT] == true || last[TIMED_OUT] == true)
        }
    }

    private fun seconds(value: Any?): Double = (value as? Number)?.toDouble() ?: 0.0

    private companion object {
        val END_KEYS = listOf("end", "endStatus")
        const val WAITED = "waitedSeconds"
        const val TIMED_OUT = "timedOut"
    }

    fun mergedWith(later: ResultRow): ResultRow {
        require(id == later.id) { "different_case: $id and ${later.id}" }
        require(parameters == later.parameters) { "different_parameters: $id: $parameters and ${later.parameters}" }
        val merged = LinkedHashMap(metrics)
        later.metrics.forEach { (metric, samples) ->
            merged[metric] = merged[metric]?.mergedWith(samples) ?: samples
        }
        val slept = if (thermalThrottleSleepSeconds == null && later.thermalThrottleSleepSeconds == null) null
            else (thermalThrottleSleepSeconds ?: 0) + (later.thermalThrottleSleepSeconds ?: 0)
        return ResultRow(id, type, algorithm, provider, operation, keySize, inputSize, keyKind, merged, parameters, slept, spanned(thermal, later.thermal),
            listOfNotNull(thermalNote, later.thermalNote).distinct().joinToString("; ").ifEmpty { null }, gated(gate, later.gate))
    }
}
