package io.github.junekim0007.cryptobench.config.global

import io.github.junekim0007.cryptobench.config.global.dto.HarnessSettings
import io.github.junekim0007.cryptobench.config.yaml.DocumentFields.expectKeys
import io.github.junekim0007.cryptobench.config.yaml.DocumentFields.number
import io.github.junekim0007.cryptobench.config.yaml.DocumentFields.optionalStringOrNull

object HarnessDocument {

    const val ITERATIONS = "iterations"
    const val WARMUP_ITERATIONS = "warmupIterations"
    const val PROFILING = "profiling"

    private val KEYS = listOf(ITERATIONS, WARMUP_ITERATIONS, PROFILING)

    fun of(harness: HarnessSettings): Map<String, Any> = LinkedHashMap<String, Any>().apply {
        harness.iterations?.let { put(ITERATIONS, it) }
        harness.warmupIterations?.let { put(WARMUP_ITERATIONS, it) }
        harness.profiling?.let { put(PROFILING, it) }
    }

    fun parse(document: Map<String, Any>, path: String): HarnessSettings {
        expectKeys(document, KEYS, path)
        return try {
            HarnessSettings(
                iterations = document[ITERATIONS]?.let { number(document, ITERATIONS).toInt() },
                warmupIterations = document[WARMUP_ITERATIONS]?.let { number(document, WARMUP_ITERATIONS).toInt() },
                profiling = optionalStringOrNull(document, PROFILING),
            )
        } catch (failure: IllegalArgumentException) {
            throw IllegalArgumentException("${failure.message} at $path", failure)
        }
    }
}
