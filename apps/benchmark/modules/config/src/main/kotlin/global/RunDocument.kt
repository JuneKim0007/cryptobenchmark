package io.github.junekim0007.cryptobench.config.global

import io.github.junekim0007.cryptobench.settings.HarnessSettings
import io.github.junekim0007.cryptobench.config.global.dto.MeasurePass
import io.github.junekim0007.cryptobench.config.global.dto.RunSettings
import io.github.junekim0007.cryptobench.config.global.dto.Warmup
import io.github.junekim0007.cryptobench.config.testset.RuleDocument
import io.github.junekim0007.cryptobench.config.yaml.DocumentFields.optionalSections
import io.github.junekim0007.cryptobench.config.yaml.DocumentFields.asSection
import io.github.junekim0007.cryptobench.config.yaml.DocumentFields.number
import io.github.junekim0007.cryptobench.config.yaml.DocumentFields.expectKeys
import io.github.junekim0007.cryptobench.config.yaml.DocumentFields.numbers
import io.github.junekim0007.cryptobench.config.yaml.DocumentFields.optional
import io.github.junekim0007.cryptobench.config.yaml.DocumentFields.optionalNumber
import io.github.junekim0007.cryptobench.config.yaml.DocumentFields.optionalSection
import io.github.junekim0007.cryptobench.config.yaml.DocumentFields.optionalString
import io.github.junekim0007.cryptobench.config.yaml.DocumentFields.strings

object RunDocument {

    private const val INPUT_SIZES = "inputSizes"
    private const val PHASES = "phases"
    private const val METRICS = "metrics"
    private const val VARIANTS = "variants"
    private const val PROCESS_REPETITIONS = "processRepetitions"
    private const val ISOLATION = "isolation"
    private const val SEED = "seed"
    private const val PASSES = "passes"
    private const val THROTTLE_SLEEP = "thermalThrottleSleepSeconds"
    private const val CASE_COOLDOWN = "caseCooldownSeconds"
    private const val WARMUP = "warmup"
    private const val THERMAL_GATE = "thermalGate"
    private const val ITERATIONS = "iterations"
    private const val JOBS = "jobs"
    private const val SAMPLES = "samples"
    private const val HARNESS = "harness"

    fun of(run: RunSettings): Map<String, Any> = linkedMapOf(
        INPUT_SIZES to run.inputSizes,
        PHASES to run.phases,
        METRICS to run.metrics,
        VARIANTS to run.variants,
        PROCESS_REPETITIONS to run.processRepetitions,
        ISOLATION to run.isolation,
        SEED to run.seed,
    ).apply {
        run.thermalThrottleSleepSeconds?.let { put(THROTTLE_SLEEP, it) }
        put(CASE_COOLDOWN, run.caseCooldownSeconds)
        put(WARMUP, linkedMapOf<String, Any>(ITERATIONS to run.warmup.iterations, JOBS to run.warmup.jobs.map { RuleDocument.of(it) }))
        run.thermalGate?.let { put(THERMAL_GATE, ThermalGateDocument.of(it)) }
        if (run.passes.isNotEmpty()) put(PASSES, run.passes.associateTo(LinkedHashMap()) { it.name to mapOf(SAMPLES to it.samples) })
 if (!run.harness.isEmpty) put(HARNESS, HarnessSettings.write(run.harness)) }

    fun parse(document: Map<String, Any>, path: String): RunSettings {
        expectKeys(document, listOf(INPUT_SIZES, PHASES, METRICS, VARIANTS, PROCESS_REPETITIONS, ISOLATION, SEED, PASSES, THROTTLE_SLEEP, CASE_COOLDOWN, WARMUP, THERMAL_GATE, HARNESS), path)
        val defaults = RunSettings()
        return RunSettings(
            inputSizes = optional(document, INPUT_SIZES, defaults.inputSizes, ::numbers),
            phases = optional(document, PHASES, defaults.phases, ::strings),
            metrics = optional(document, METRICS, defaults.metrics, ::strings),
            variants = optional(document, VARIANTS, defaults.variants, ::strings),
            processRepetitions = optionalNumber(document, PROCESS_REPETITIONS)?.toInt() ?: defaults.processRepetitions,
            isolation = optionalString(document, ISOLATION).ifEmpty { defaults.isolation },
            seed = optionalNumber(document, SEED)?.toLong() ?: defaults.seed,
            thermalThrottleSleepSeconds = optionalNumber(document, THROTTLE_SLEEP)?.toInt(),
            caseCooldownSeconds = optionalNumber(document, CASE_COOLDOWN)?.toInt() ?: defaults.caseCooldownSeconds,
            warmup = optionalSection(document, WARMUP)?.let { warmup(it, "$path.$WARMUP") } ?: defaults.warmup,
            thermalGate = optionalSection(document, THERMAL_GATE)?.let { ThermalGateDocument.parse(it, "$path.$THERMAL_GATE") },
            passes = optionalSection(document, PASSES)?.let { passes(it, "$path.$PASSES") } ?: defaults.passes,
            harness = optionalSection(document, HARNESS)?.let { HarnessSettings.read(it, "$path.$HARNESS") } ?: HarnessSettings(),
        )
    }

    private fun warmup(document: Map<String, Any>, path: String): Warmup {
        expectKeys(document, listOf(ITERATIONS, JOBS), path)
        return Warmup(optionalNumber(document, ITERATIONS)?.toInt() ?: Warmup.ITERATIONS, RuleDocument.parseList(optionalSections(document, JOBS), "$path.$JOBS"))
    }

    private fun passes(document: Map<String, Any>, path: String): List<MeasurePass> = document.keys.map { name ->
        val pass = asSection(document.getValue(name), "$path.$name")
        expectKeys(pass, listOf(SAMPLES), "$path.$name")
        MeasurePass(name, number(pass, SAMPLES).toInt())
    }
}
