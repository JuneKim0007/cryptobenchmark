package io.github.junekim0007.cryptobench.config.harness

import io.github.junekim0007.cryptobench.config.yaml.DocumentFields.expectKeys
import io.github.junekim0007.cryptobench.config.yaml.DocumentFields.optionalNumber
import io.github.junekim0007.cryptobench.config.yaml.DocumentFields.optionalStringOrNull
import io.github.junekim0007.cryptobench.config.yaml.DocumentFields.withPathInFailure

object HarnessDocument {

    private const val ITERATIONS = "iterations"
    private const val WARMUP_ITERATIONS = "warmupIterations"
    private const val PROFILING = "profiling"

    private val KEYS = listOf(ITERATIONS, WARMUP_ITERATIONS, PROFILING)

    fun of(harness: HarnessSettings): Map<String, Any> = LinkedHashMap<String, Any>().apply {
        harness.iterations?.let { put(ITERATIONS, it) }
        harness.warmupIterations?.let { put(WARMUP_ITERATIONS, it) }
        harness.profiling?.let { put(PROFILING, it) }
    }

    fun parse(document: Map<String, Any>, path: String): HarnessSettings {
        expectKeys(document, KEYS, path)
        return withPathInFailure(path) {
            HarnessSettings(
                iterations = optionalNumber(document, ITERATIONS)?.toInt(),
                warmupIterations = optionalNumber(document, WARMUP_ITERATIONS)?.toInt(),
                profiling = optionalStringOrNull(document, PROFILING),
            )
        }
    }
}
