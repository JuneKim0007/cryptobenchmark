package io.github.junekim0007.cryptobench.config.global

import io.github.junekim0007.cryptobench.config.entry.Variants
import io.github.junekim0007.cryptobench.settings.EnergySettings
import io.github.junekim0007.cryptobench.settings.HarnessSettings
import io.github.junekim0007.cryptobench.settings.RunKeys
import io.github.junekim0007.cryptobench.settings.RunKeys.CASE_COOLDOWN
import io.github.junekim0007.cryptobench.settings.RunKeys.HARNESS
import io.github.junekim0007.cryptobench.settings.RunKeys.INPUT_SIZES
import io.github.junekim0007.cryptobench.settings.RunKeys.LAUNCH_RETRIES
import io.github.junekim0007.cryptobench.settings.RunKeys.METRICS
import io.github.junekim0007.cryptobench.settings.RunKeys.ORDER_SEED
import io.github.junekim0007.cryptobench.settings.RunKeys.PASSES
import io.github.junekim0007.cryptobench.settings.RunKeys.PHASES
import io.github.junekim0007.cryptobench.settings.RunKeys.PROCESS_REPETITIONS
import io.github.junekim0007.cryptobench.settings.RunKeys.RESUME_BLOCK_RUNS
import io.github.junekim0007.cryptobench.settings.RunKeys.SEED
import io.github.junekim0007.cryptobench.settings.RunKeys.THERMAL_GATE
import io.github.junekim0007.cryptobench.settings.RunKeys.THROTTLE_SLEEP
import io.github.junekim0007.cryptobench.settings.RunKeys.VARIANTS
import io.github.junekim0007.cryptobench.settings.RunKeys.WARMUP
import io.github.junekim0007.cryptobench.config.global.dto.MeasurePass
import io.github.junekim0007.cryptobench.config.global.dto.RunSettings
import io.github.junekim0007.cryptobench.config.global.dto.ThermalGate
import io.github.junekim0007.cryptobench.config.global.dto.Warmup
import io.github.junekim0007.cryptobench.config.testset.RuleDocument
import io.github.junekim0007.cryptobench.document.DocumentFields.optionalSections
import io.github.junekim0007.cryptobench.document.DocumentFields.asSection
import io.github.junekim0007.cryptobench.document.DocumentFields.number
import io.github.junekim0007.cryptobench.document.DocumentFields.expectKeys
import io.github.junekim0007.cryptobench.document.DocumentFields.numbers
import io.github.junekim0007.cryptobench.document.DocumentFields.optional
import io.github.junekim0007.cryptobench.document.DocumentFields.optionalNumber
import io.github.junekim0007.cryptobench.document.DocumentFields.optionalSection
import io.github.junekim0007.cryptobench.document.DocumentFields.strings

object RunDocument {

    private const val ITERATIONS = "iterations"
    private const val JOBS = "jobs"
    private const val CASES = "cases"
    private const val SAMPLES = "samples"
    private const val MIN_WINDOW_SECONDS = "minWindowSeconds"

    fun of(run: RunSettings): Map<String, Any> = linkedMapOf(
        INPUT_SIZES to run.inputSizes,
        PHASES to run.phases,
        METRICS to run.metrics,
        VARIANTS to run.variants,
        PROCESS_REPETITIONS to run.processRepetitions,
        SEED to run.seed,
    ).apply {
        run.thermalThrottleSleepSeconds?.let { put(THROTTLE_SLEEP, it) }
        put(CASE_COOLDOWN, run.caseCooldownSeconds)
        put(LAUNCH_RETRIES, run.launchRetries)
        put(RESUME_BLOCK_RUNS, run.resumeBlockRuns)
        put(ORDER_SEED, run.orderSeed)
        put(WARMUP, linkedMapOf<String, Any>(ITERATIONS to run.warmup.iterations, JOBS to run.warmup.jobs.map { RuleDocument.of(it) }, CASES to run.warmup.cases))
        run.thermalGate?.let { put(THERMAL_GATE, ThermalGate.GATE.write(it)) }
        if (run.passes.isNotEmpty()) put(PASSES, run.passes.associateTo(LinkedHashMap()) { pass ->
            pass.name to linkedMapOf<String, Any>(SAMPLES to pass.samples).apply { pass.minWindowSeconds?.let { put(MIN_WINDOW_SECONDS, it) } } })
 if (!run.harness.isEmpty) put(HARNESS, HarnessSettings.write(run.harness)) }

    /** What of() writes for a run that sets nothing, with the gate's and the energy keys' defaults a block without them gets; orderSeed has none. */
    fun defaults(): Map<String, Any> = of(RunSettings(orderSeed = 0L, thermalGate = ThermalGate.DEFAULTS)) - ORDER_SEED +
        (HARNESS to HarnessSettings.write(HarnessSettings(energy = EnergySettings(capture = EnergySettings.CAPTURES.first(), source = EnergySettings.RAILS))))

    fun parse(document: Map<String, Any>, path: String): RunSettings {
        expectKeys(document, RunKeys.ALL, path)
        val orderSeed = optionalNumber(document, ORDER_SEED)?.toLong() ?: throw IllegalArgumentException("missing_field: $path.$ORDER_SEED")
        val defaults = RunSettings(orderSeed = orderSeed)
        return RunSettings(
            inputSizes = optional(document, INPUT_SIZES, defaults.inputSizes, ::numbers),
            phases = optional(document, PHASES, defaults.phases, ::strings),
            metrics = optional(document, METRICS, defaults.metrics, ::strings),
            variants = Variants.read(document, VARIANTS, "$path.$VARIANTS")?.values ?: defaults.variants,
            processRepetitions = optionalNumber(document, PROCESS_REPETITIONS)?.toInt() ?: defaults.processRepetitions,
            seed = optionalNumber(document, SEED)?.toLong() ?: defaults.seed,
            thermalThrottleSleepSeconds = optionalNumber(document, THROTTLE_SLEEP)?.toInt(),
            caseCooldownSeconds = optionalNumber(document, CASE_COOLDOWN)?.toInt() ?: defaults.caseCooldownSeconds,
            launchRetries = optionalNumber(document, LAUNCH_RETRIES)?.toInt() ?: defaults.launchRetries,
            resumeBlockRuns = optionalNumber(document, RESUME_BLOCK_RUNS)?.toInt() ?: defaults.resumeBlockRuns,
            orderSeed = orderSeed,
            warmup = optionalSection(document, WARMUP)?.let { warmup(it, "$path.$WARMUP") } ?: defaults.warmup,
            thermalGate = optionalSection(document, THERMAL_GATE)?.let { ThermalGate.GATE.read(it, "$path.$THERMAL_GATE").resolved(ThermalGate.DEFAULTS, "$path.$THERMAL_GATE") },
            passes = optionalSection(document, PASSES)?.let { passes(it, "$path.$PASSES") } ?: defaults.passes,
            harness = optionalSection(document, HARNESS)?.let { HarnessSettings.read(it, "$path.$HARNESS") } ?: HarnessSettings(),
        )
    }

    fun notices(document: Map<String, Any>, path: String): List<String> = listOfNotNull(Variants.read(document, VARIANTS, "$path.$VARIANTS")?.notice)

    private fun warmup(document: Map<String, Any>, path: String): Warmup {
        expectKeys(document, listOf(ITERATIONS, JOBS, CASES), path)
        return Warmup(optionalNumber(document, ITERATIONS)?.toInt() ?: Warmup.ITERATIONS, RuleDocument.parseList(optionalSections(document, JOBS), "$path.$JOBS"),
            optionalNumber(document, CASES)?.toInt() ?: Warmup.CASES)
    }

    private fun passes(document: Map<String, Any>, path: String): List<MeasurePass> = document.keys.map { name ->
        val pass = asSection(document.getValue(name), "$path.$name")
        expectKeys(pass, listOf(SAMPLES, MIN_WINDOW_SECONDS), "$path.$name")
        val samples = number(pass, SAMPLES).toInt()
        optionalNumber(pass, MIN_WINDOW_SECONDS)?.let { MeasurePass(name, samples, it.toInt()) } ?: MeasurePass(name, samples)
    }
}
