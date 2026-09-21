package io.github.junekim0007.cryptobench.preparation.request

import io.github.junekim0007.cryptobench.preparation.measurement.Metric
import io.github.junekim0007.cryptobench.preparation.measurement.Phase

data class BenchmarkRequest(
    val selections: List<Selection>,
    val inputSizes: List<Int> = listOf(DEFAULT_INPUT_SIZE),
    val phases: Set<Phase> = setOf(Phase.WARM),
    val metrics: Set<Metric> = setOf(Metric.TIME),
    val processRepetitions: Int = 1,
    val seed: Long = 0L,
    val onFailure: OnFailure = OnFailure.SKIP,
) {

    init {
        require(selections.isNotEmpty()) { "missing_field: selections" }
        require(selections.size == selections.distinct().size) { "duplicate: selections" }
        require(inputSizes.isNotEmpty()) { "missing_field: inputSizes" }
        require(inputSizes.all { it > 0 }) { "not_positive: inputSizes $inputSizes" }
        require(inputSizes.size == inputSizes.distinct().size) { "duplicate: inputSizes $inputSizes" }
        require(phases.isNotEmpty()) { "missing_field: phases" }
        require(metrics.isNotEmpty()) { "missing_field: metrics" }
        require(processRepetitions >= 1) { "not_positive: processRepetitions $processRepetitions" }
    }

    companion object {
        const val DEFAULT_INPUT_SIZE = 1024
    }
}
