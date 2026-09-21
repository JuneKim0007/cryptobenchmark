package io.github.junekim0007.cryptobench.config.global.dto

/** The `run` section. Phases and metrics stay names; preparation decides what they mean. */
data class RunSettings(
    val inputSizes: List<Int> = listOf(1024),
    val phases: List<String> = listOf("WARM"),
    val metrics: List<String> = listOf("TIME"),
    val processRepetitions: Int = 1,
    val seed: Long = 0L,
) {

    init {
        require(inputSizes.isNotEmpty() && inputSizes.all { it > 0 }) { "invalid: inputSizes $inputSizes" }
        require(phases.isNotEmpty() && phases.none { it.isBlank() }) { "invalid: phases $phases" }
        require(metrics.isNotEmpty() && metrics.none { it.isBlank() }) { "invalid: metrics $metrics" }
        require(processRepetitions >= 1) { "not_positive: processRepetitions $processRepetitions" }
    }
}
