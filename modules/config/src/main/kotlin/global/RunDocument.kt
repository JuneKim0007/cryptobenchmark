package io.github.junekim0007.cryptobench.config.global

import io.github.junekim0007.cryptobench.config.global.dto.HarnessSettings
import io.github.junekim0007.cryptobench.config.global.dto.RunSettings
import io.github.junekim0007.cryptobench.config.yaml.DocumentFields.expectKeys
import io.github.junekim0007.cryptobench.config.yaml.DocumentFields.numbers
import io.github.junekim0007.cryptobench.config.yaml.DocumentFields.optional
import io.github.junekim0007.cryptobench.config.yaml.DocumentFields.optionalNumber
import io.github.junekim0007.cryptobench.config.yaml.DocumentFields.optionalSection
import io.github.junekim0007.cryptobench.config.yaml.DocumentFields.strings

object RunDocument {

    private const val INPUT_SIZES = "inputSizes"
    private const val PHASES = "phases"
    private const val METRICS = "metrics"
    private const val PROCESS_REPETITIONS = "processRepetitions"
    private const val SEED = "seed"
    private const val HARNESS = "harness"

    fun of(run: RunSettings): Map<String, Any> = linkedMapOf(
        INPUT_SIZES to run.inputSizes,
        PHASES to run.phases,
        METRICS to run.metrics,
        PROCESS_REPETITIONS to run.processRepetitions,
        SEED to run.seed,
    ).apply { if (!run.harness.isEmpty) put(HARNESS, HarnessDocument.of(run.harness)) }

    fun parse(document: Map<String, Any>, path: String): RunSettings {
        expectKeys(document, listOf(INPUT_SIZES, PHASES, METRICS, PROCESS_REPETITIONS, SEED, HARNESS), path)
        val defaults = RunSettings()
        return RunSettings(
            inputSizes = optional(document, INPUT_SIZES, defaults.inputSizes, ::numbers),
            phases = optional(document, PHASES, defaults.phases, ::strings),
            metrics = optional(document, METRICS, defaults.metrics, ::strings),
            processRepetitions = optionalNumber(document, PROCESS_REPETITIONS)?.toInt() ?: defaults.processRepetitions,
            seed = optionalNumber(document, SEED)?.toLong() ?: defaults.seed,
            harness = optionalSection(document, HARNESS)?.let { HarnessDocument.parse(it, "$path.$HARNESS") } ?: HarnessSettings(),
        )
    }
}
