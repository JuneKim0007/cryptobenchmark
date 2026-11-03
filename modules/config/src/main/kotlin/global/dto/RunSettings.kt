package io.github.junekim0007.cryptobench.config.global.dto

import io.github.junekim0007.cryptobench.settings.HarnessSettings
import io.github.junekim0007.cryptobench.settings.Metric

data class RunSettings(
    val inputSizes: List<Int> = listOf(1024),
    val phases: List<String> = listOf("WARM"),
    val metrics: List<String> = listOf("TIME"),
    val processRepetitions: Int = 1,
    // case: one device process per measured case, so a case that kills its process loses only itself
    val isolation: String = CASE,
    val seed: Long = 0L,
    // before/after runs: processes per side, run in alternating order so linear drift does not land on one side
    val scopedRepetitions: Int = 3,
    val harness: HarnessSettings = HarnessSettings(),
) {

    init {
        require(inputSizes.isNotEmpty() && inputSizes.all { it > 0 }) { "invalid: inputSizes $inputSizes" }
        require(phases.isNotEmpty() && phases.none { it.isBlank() }) { "invalid: phases $phases" }
        Metric.read(metrics, "run.metrics")
        require(processRepetitions >= 1) { "not_positive: processRepetitions $processRepetitions" }
        require(scopedRepetitions >= 1) { "not_positive: scopedRepetitions $scopedRepetitions" }
        require(isolation in ISOLATIONS) { "invalid: run.isolation $isolation, expected one of $ISOLATIONS" }
    }

    companion object {
        const val CASE = "case"
        val ISOLATIONS = listOf(CASE, "run")
    }
}
