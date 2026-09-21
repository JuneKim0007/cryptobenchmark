package io.github.junekim0007.cryptobench.config.global

import io.github.junekim0007.cryptobench.config.global.dto.RunSettings
import io.github.junekim0007.cryptobench.config.yaml.DocumentFields.expectKeys
import io.github.junekim0007.cryptobench.config.yaml.DocumentFields.number
import io.github.junekim0007.cryptobench.config.yaml.DocumentFields.numbers
import io.github.junekim0007.cryptobench.config.yaml.DocumentFields.strings

/** The `run` section, shared by global.yaml (as written) and effective.yaml (as frozen). */
object RunDocument {

    private const val INPUT_SIZES = "inputSizes"
    private const val PHASES = "phases"
    private const val METRICS = "metrics"
    private const val PROCESS_REPETITIONS = "processRepetitions"
    private const val SEED = "seed"

    fun of(run: RunSettings): Map<String, Any> = linkedMapOf(
        INPUT_SIZES to run.inputSizes,
        PHASES to run.phases,
        METRICS to run.metrics,
        PROCESS_REPETITIONS to run.processRepetitions,
        SEED to run.seed,
    )

    /** Every key is optional in a hand-written section; a missing one keeps its default. */
    fun parse(document: Map<String, Any>, path: String): RunSettings {
        expectKeys(document, listOf(INPUT_SIZES, PHASES, METRICS, PROCESS_REPETITIONS, SEED), path)
        val defaults = RunSettings()
        return RunSettings(
            inputSizes = if (document.containsKey(INPUT_SIZES)) numbers(document, INPUT_SIZES) else defaults.inputSizes,
            phases = if (document.containsKey(PHASES)) strings(document, PHASES) else defaults.phases,
            metrics = if (document.containsKey(METRICS)) strings(document, METRICS) else defaults.metrics,
            processRepetitions = if (document.containsKey(PROCESS_REPETITIONS)) number(document, PROCESS_REPETITIONS).toInt() else defaults.processRepetitions,
            seed = if (document.containsKey(SEED)) number(document, SEED).toLong() else defaults.seed,
        )
    }
}
