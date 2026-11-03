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
    // empty: one pass measures every metric; else one device session per metric group, merged per metric
    val passes: List<MeasurePass> = emptyList(),
    // androidx.benchmark.thermalThrottle.sleepDurationSeconds on the device; null keeps Jetpack's default
    val thermalThrottleSleepSeconds: Int? = null,
    // host sleep before every measured case but a session's first, so heat from one case does not land on the next
    val caseCooldownSeconds: Int = 0,
    val warmup: Warmup = Warmup(),
    // null: no gate, the run starts every case as soon as the last one ends
    val thermalGate: ThermalGate? = null,
    val harness: HarnessSettings = HarnessSettings(),
) {

    init {
        require(inputSizes.isNotEmpty() && inputSizes.all { it > 0 }) { "invalid: inputSizes $inputSizes" }
        require(phases.isNotEmpty() && phases.none { it.isBlank() }) { "invalid: phases $phases" }
        Metric.read(metrics, "run.metrics")
        require(processRepetitions >= 1) { "not_positive: processRepetitions $processRepetitions" }
        require(scopedRepetitions >= 1) { "not_positive: scopedRepetitions $scopedRepetitions" }
        require(passes.map { it.name }.toSet().size == passes.size) { "duplicate: run.passes ${passes.map { it.name }}" }
        require(passes.isEmpty() || passes.any { it.name == MeasurePass.TIMING }) {
            "missing_pass: run.passes ${passes.map { it.name }}, timing is the pass every other merges into"
        }
        require(passes.none { it.name == MeasurePass.ALLOCATION } || "ALLOCATION" in metrics) {
            "pass_without_metric: run.passes.allocation measures ALLOCATION, which run.metrics $metrics does not report"
        }
        require(thermalThrottleSleepSeconds == null || thermalThrottleSleepSeconds >= 0) { "negative: thermalThrottleSleepSeconds $thermalThrottleSleepSeconds" }
        require(caseCooldownSeconds >= 0) { "negative: caseCooldownSeconds $caseCooldownSeconds" }
        require(isolation in ISOLATIONS) { "invalid: run.isolation $isolation, expected one of $ISOLATIONS" }
    }

    companion object {
        const val CASE = "case"
        val ISOLATIONS = listOf(CASE, "run")
    }
}
