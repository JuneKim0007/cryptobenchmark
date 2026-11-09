package io.github.junekim0007.cryptobench.config.global.dto

import io.github.junekim0007.cryptobench.settings.HarnessSettings
import io.github.junekim0007.cryptobench.settings.Metric

data class RunSettings(
    val inputSizes: List<Int> = listOf(1024),
    val phases: List<String> = listOf("WARM"),
    val metrics: List<String> = listOf("TIME"),
    // each measured item once per variant: fixed keeps the setup the API lets a call keep, notFixed makes it every call
    val variants: List<String> = VARIANTS,
    val processRepetitions: Int = 1,
    // case: one device process per measured case, so a case that kills its process loses only itself
    val isolation: String = CASE,
    val seed: Long = 0L,
    // empty: one pass measures every metric; else one device session per metric group, merged per metric
    val passes: List<MeasurePass> = emptyList(),
    // androidx.benchmark.thermalThrottle.sleepDurationSeconds on the device; null keeps Jetpack's default
    val thermalThrottleSleepSeconds: Int? = null,
    // host sleep before every measured case but a session's first, so heat from one case does not land on the next
    val caseCooldownSeconds: Int = 0,
    val warmup: Warmup = Warmup(),
    // null: no gate, the run starts every case as soon as the last one ends
    val thermalGate: ThermalGate? = null,
    // a run of a case that failed for a reason other than heat is launched this many more times, then the next case goes on
    val launchRetries: Int = LAUNCH_RETRIES,
    val harness: HarnessSettings = HarnessSettings(),
) {

    init {
        require(inputSizes.isNotEmpty() && inputSizes.all { it > 0 }) { "invalid: inputSizes $inputSizes" }
        require(phases.isNotEmpty() && phases.none { it.isBlank() }) { "invalid: phases $phases" }
        Metric.read(metrics, "run.metrics")
        require(variants.isNotEmpty() && variants.all { it in VARIANTS } && variants.distinct().size == variants.size) {
            "invalid: run.variants $variants, expected distinct values of $VARIANTS"
        }
        require(processRepetitions >= 1) { "not_positive: processRepetitions $processRepetitions" }
        require(passes.map { it.name }.toSet().size == passes.size) { "duplicate: run.passes ${passes.map { it.name }}" }
        require(passes.isEmpty() || passes.any { it.name == MeasurePass.TIMING }) {
            "missing_pass: run.passes ${passes.map { it.name }}, timing is the pass every other merges into"
        }
        require(passes.none { it.name == MeasurePass.ALLOCATION } || "ALLOCATION" in metrics) {
            "pass_without_metric: run.passes.allocation measures ALLOCATION, which run.metrics $metrics does not report"
        }
        require(thermalThrottleSleepSeconds == null || thermalThrottleSleepSeconds >= 0) { "negative: thermalThrottleSleepSeconds $thermalThrottleSleepSeconds" }
        require(caseCooldownSeconds >= 0) { "negative: caseCooldownSeconds $caseCooldownSeconds" }
        require(launchRetries >= 0) { "negative: launchRetries $launchRetries" }
        require(thermalGate == null || isolation == CASE) { "invalid: run.thermalGate needs run.isolation $CASE, a whole-session process has no single run to discard" }
        require(isolation in ISOLATIONS) { "invalid: run.isolation $isolation, expected one of $ISOLATIONS" }
    }

    companion object {
        const val CASE = "case"
        const val LAUNCH_RETRIES = 2
        val ISOLATIONS = listOf(CASE, "run")
        val VARIANTS = listOf("fixed", "notFixed")
    }
}
