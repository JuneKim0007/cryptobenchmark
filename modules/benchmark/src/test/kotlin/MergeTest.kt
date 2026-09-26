package io.github.junekim0007.cryptobench.benchmark

import io.github.junekim0007.cryptobench.benchmark.report.Merge
import org.junit.Assert.assertEquals
import org.junit.Test

class MergeTest {

    private fun text(id: String, vararg samples: Long) = """
        {"runtime": {"model": "Pixel 9"},
         "cases": [{"id": "$id", "type": "MessageDigest", "algorithm": "SHA-256", "provider": "SUN",
                    "operation": "DIGEST", "keySize": null, "inputSize": 1024, "iterations": 8192,
                    "nanosPerOperation": [${samples.joinToString(", ")}]}]}
    """.trimIndent()

    /** Process-to-process variance is the reason processRepetitions exists: the samples must not be averaged away. */
    @Test
    fun aCaseKeepsEveryProcessSamples() {
        val merged = Merge.merge(listOf(text("digest", 10, 11), text("digest", 20, 21, 22)))
        assertEquals(1, merged.rows.size)
        assertEquals(listOf(10L, 11L, 20L, 21L, 22L), merged.rows.single().nanosPerOperation)
        assertEquals(2, merged.processes)
        assertEquals(mapOf("model" to "Pixel 9"), merged.runtime)
    }

    /** A case one process skipped still carries what the others measured, in first-seen order. */
    @Test
    fun aCaseMissingFromOneProcessSurvives() {
        val merged = Merge.merge(listOf(text("digest", 10), text("mac", 20)))
        assertEquals(listOf("digest", "mac"), merged.rows.map { it.id })
    }
}
