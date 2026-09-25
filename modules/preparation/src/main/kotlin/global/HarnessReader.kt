package io.github.junekim0007.cryptobench.preparation.global

import io.github.junekim0007.cryptobench.preparation.shared.DocumentFields.expectKeys
import io.github.junekim0007.cryptobench.preparation.shared.DocumentFields.number
import io.github.junekim0007.cryptobench.preparation.shared.DocumentFields.string

object HarnessReader {

    private const val ITERATIONS = "iterations"
    private const val WARMUP_ITERATIONS = "warmupIterations"
    private const val PROFILING = "profiling"

    fun read(document: Map<String, Any>, path: String): HarnessSettings {
        expectKeys(document, listOf(ITERATIONS, WARMUP_ITERATIONS, PROFILING), path)
        return try {
            HarnessSettings(
                iterations = document[ITERATIONS]?.let { number(document, ITERATIONS).toInt() },
                warmupIterations = document[WARMUP_ITERATIONS]?.let { number(document, WARMUP_ITERATIONS).toInt() },
                profiling = document[PROFILING]?.let { string(document, PROFILING) },
            )
        } catch (failure: IllegalArgumentException) {
            throw IllegalArgumentException("${failure.message} at $path", failure)
        }
    }
}
