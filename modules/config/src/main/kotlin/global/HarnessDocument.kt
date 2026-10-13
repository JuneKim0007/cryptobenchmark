package io.github.junekim0007.cryptobench.config.global

import io.github.junekim0007.cryptobench.config.global.dto.EnergySettings
import io.github.junekim0007.cryptobench.config.global.dto.HarnessSettings
import io.github.junekim0007.cryptobench.config.yaml.DocumentFields.expectKeys
import io.github.junekim0007.cryptobench.config.yaml.DocumentFields.optionalNumber
import io.github.junekim0007.cryptobench.config.yaml.DocumentFields.optionalSection
import io.github.junekim0007.cryptobench.config.yaml.DocumentFields.optionalStringOrNull
import io.github.junekim0007.cryptobench.config.yaml.DocumentFields.withPathInFailure

object HarnessDocument {

    private const val ITERATIONS = "iterations"
    private const val WARMUP_ITERATIONS = "warmupIterations"
    private const val PROFILING = "profiling"
    private const val ENERGY = "energy"

    private val KEYS = listOf(ITERATIONS, WARMUP_ITERATIONS, PROFILING, ENERGY)

    fun of(harness: HarnessSettings): Map<String, Any> = LinkedHashMap<String, Any>().apply {
        harness.iterations?.let { put(ITERATIONS, it) }
        harness.warmupIterations?.let { put(WARMUP_ITERATIONS, it) }
        harness.profiling?.let { put(PROFILING, it) }
        if (!harness.energy.isEmpty) put(ENERGY, EnergyDocument.of(harness.energy))
    }

    fun parse(document: Map<String, Any>, path: String): HarnessSettings {
        expectKeys(document, KEYS, path)
        // Parsed outside the path wrapper: the energy block names its own, deeper path.
        val energy = optionalSection(document, ENERGY)?.let { EnergyDocument.parse(it, "$path.$ENERGY") } ?: EnergySettings()
        return withPathInFailure(path) {
            HarnessSettings(
                iterations = optionalNumber(document, ITERATIONS)?.toInt(),
                warmupIterations = optionalNumber(document, WARMUP_ITERATIONS)?.toInt(),
                profiling = optionalStringOrNull(document, PROFILING),
                energy = energy,
            )
        }
    }
}
