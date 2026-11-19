package io.github.junekim0007.cryptobench.preparation.global

import io.github.junekim0007.cryptobench.settings.OnFailure
import io.github.junekim0007.cryptobench.settings.HarnessSettings

import io.github.junekim0007.cryptobench.settings.Metric
import io.github.junekim0007.cryptobench.settings.Phase
import io.github.junekim0007.cryptobench.preparation.measurement.Variant

data class GlobalSettings(
    val inputSizes: List<Int>,
    val phases: Set<Phase>,
    val metrics: Set<Metric>,
    val processRepetitions: Int,
    val seed: Long,
    val onFailure: OnFailure,
    val harness: HarnessSettings = HarnessSettings(),
    val variants: List<Variant>,
) {

    fun inputSizesFor(entryInputSizes: List<Int>): List<Int> = entryInputSizes.ifEmpty { inputSizes }
}
