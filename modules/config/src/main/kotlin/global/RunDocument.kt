package io.github.junekim0007.cryptobench.config.global

import io.github.junekim0007.cryptobench.config.global.dto.RunSettings
import io.github.junekim0007.cryptobench.config.yaml.DocumentFields.expectKeys
import io.github.junekim0007.cryptobench.config.yaml.DocumentFields.number
import io.github.junekim0007.cryptobench.config.yaml.DocumentFields.numbers
import io.github.junekim0007.cryptobench.config.yaml.DocumentFields.optional
import io.github.junekim0007.cryptobench.config.yaml.DocumentFields.strings

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

    fun parse(document: Map<String, Any>, path: String): RunSettings {
        expectKeys(document, listOf(INPUT_SIZES, PHASES, METRICS, PROCESS_REPETITIONS, SEED), path)
        val defaults = RunSettings()
        return RunSettings(
            inputSizes = optional(document, INPUT_SIZES, defaults.inputSizes, ::numbers),
            phases = optional(document, PHASES, defaults.phases, ::strings),
            metrics = optional(document, METRICS, defaults.metrics, ::strings),
            processRepetitions = optional(document, PROCESS_REPETITIONS, defaults.processRepetitions) { section, key -> number(section, key).toInt() },
            seed = optional(document, SEED, defaults.seed) { section, key -> number(section, key).toLong() },
        )
    }
}
