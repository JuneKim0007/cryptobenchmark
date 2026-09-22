package io.github.junekim0007.cryptobench.preparation.global

import io.github.junekim0007.cryptobench.preparation.measurement.Metric
import io.github.junekim0007.cryptobench.preparation.measurement.Phase

data class GlobalSettings(
    val inputSizes: List<Int>,
    val phases: Set<Phase>,
    val metrics: Set<Metric>,
    val processRepetitions: Int,
    val seed: Long,
    val onFailure: OnFailure,
) {

    init {
        require(inputSizes.isNotEmpty()) { "missing_field: inputSizes" }
        require(inputSizes.all { it > 0 }) { "not_positive: inputSizes $inputSizes" }
        require(inputSizes.size == inputSizes.distinct().size) { "duplicate: inputSizes $inputSizes" }
        require(phases.isNotEmpty()) { "missing_field: phases" }
        require(metrics.isNotEmpty()) { "missing_field: metrics" }
        require(processRepetitions >= 1) { "not_positive: processRepetitions $processRepetitions" }
    }

    fun inputSizesFor(entryInputSizes: List<Int>): List<Int> = entryInputSizes.ifEmpty { inputSizes }
}
