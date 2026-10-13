package io.github.junekim0007.cryptobench.benchmark

import io.github.junekim0007.cryptobench.benchmark.report.Merge
import io.github.junekim0007.cryptobench.benchmark.report.MetricSamples
import org.junit.Assert.assertEquals
import org.junit.Test

class MergeTest {

    private fun legacy(id: String, vararg samples: Long) = """
        {"runtime": {"model": "Pixel 9"},
         "cases": [{"id": "$id", "type": "MessageDigest", "algorithm": "SHA-256", "provider": "SUN",
                    "operation": "DIGEST", "keySize": null, "inputSize": 1024, "iterations": 8192,
                    "nanosPerOperation": [${samples.joinToString(", ")}]}]}
    """.trimIndent()

    private fun text(id: String, time: List<Double>, allocations: List<Double>? = null): String {
        val metrics = buildList {
            add("\"timeNs\": {\"iterations\": 8192, \"runs\": [${time.joinToString(", ")}]}")
            if (allocations != null) {
                add("\"allocationCount\": {\"iterations\": 1, \"runs\": [${allocations.joinToString(", ")}]}")
            }
        }
        return """
            {"runtime": {"model": "Pixel 9"},
             "cases": [{"id": "$id", "type": "MessageDigest", "algorithm": "SHA-256", "provider": "SUN",
                        "operation": "DIGEST", "keySize": null, "inputSize": 1024,
                        "metrics": {${metrics.joinToString(", ")}}}]}
        """.trimIndent()
    }

    @Test
    fun aCaseKeepsEveryProcessSamples() {
        val merged = Merge.merge(listOf(text("digest", listOf(10.0, 11.0)), text("digest", listOf(20.0, 21.0, 22.0))))
        assertEquals(1, merged.rows.size)
        assertEquals(listOf(10.0, 11.0, 20.0, 21.0, 22.0), merged.rows.single().time?.runs)
        assertEquals(2, merged.processes)
        assertEquals(mapOf("model" to "Pixel 9"), merged.runtime)
    }

    @Test
    fun everyMetricIsMergedOnItsOwnKey() {
        val merged = Merge.merge(
            listOf(
                text("digest", listOf(10.0, 11.0), allocations = listOf(2.0, 2.0)),
                text("digest", listOf(20.0, 21.0), allocations = listOf(3.0, 2.0)),
            ),
        )
        val row = merged.rows.single()
        assertEquals(listOf(MetricSamples.TIME, MetricSamples.ALLOCATIONS), row.metrics.keys.toList())
        assertEquals(MetricSamples(listOf(10.0, 11.0, 20.0, 21.0), 8192), row.metrics[MetricSamples.TIME])
        assertEquals(MetricSamples(listOf(2.0, 2.0, 3.0, 2.0), 1), row.metrics[MetricSamples.ALLOCATIONS])
    }

    @Test
    fun aMetricOnlyOneProcessMeasuredSurvives() {
        val merged = Merge.merge(listOf(text("digest", listOf(10.0), allocations = listOf(2.0)), text("digest", listOf(20.0))))
        assertEquals(MetricSamples(listOf(2.0), 1), merged.rows.single().metrics[MetricSamples.ALLOCATIONS])
        assertEquals(listOf(10.0, 20.0), merged.rows.single().time?.runs)
    }

    @Test
    fun aFileWithOnlyTheFlatPairIsStillRead() {
        val merged = Merge.merge(listOf(legacy("digest", 10, 11), text("digest", listOf(20.0))))
        assertEquals(MetricSamples(listOf(10.0, 11.0, 20.0), 8192), merged.rows.single().time)
    }

    @Test
    fun aCaseMissingFromOneProcessSurvives() {
        val merged = Merge.merge(listOf(text("digest", listOf(10.0)), text("mac", listOf(20.0))))
        assertEquals(listOf("digest", "mac"), merged.rows.map { it.id })
    }
}
