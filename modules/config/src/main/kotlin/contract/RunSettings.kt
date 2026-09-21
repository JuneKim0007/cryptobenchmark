package io.github.junekim0007.cryptobench.config.contract

/** Settings every entry inherits. Phases and metrics stay names here; the benchmark decides what they mean. */
data class RunSettings(
    val inputSizes: List<Int>,
    val phases: List<String>,
    val metrics: List<String>,
    val processRepetitions: Int,
    val seed: Long,
) {

    init {
        require(inputSizes.isNotEmpty() && inputSizes.all { it > 0 }) { "invalid: inputSizes $inputSizes" }
        require(phases.isNotEmpty() && phases.none { it.isBlank() }) { "invalid: phases $phases" }
        require(metrics.isNotEmpty() && metrics.none { it.isBlank() }) { "invalid: metrics $metrics" }
        require(processRepetitions >= 1) { "not_positive: processRepetitions $processRepetitions" }
    }
}
