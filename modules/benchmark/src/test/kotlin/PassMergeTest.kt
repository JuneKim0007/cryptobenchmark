package io.github.junekim0007.cryptobench.benchmark

import io.github.junekim0007.cryptobench.benchmark.report.MetricSamples
import io.github.junekim0007.cryptobench.benchmark.report.PassMerge
import io.github.junekim0007.cryptobench.benchmark.report.jetpack.JetpackResults
import org.junit.Assert.assertEquals
import org.junit.Test
import java.io.File

/** Each metric of the merged file comes from the pass that measured it, never from another pass, and a pass can ask for its own samples. */
class PassMergeTest {

    private fun text(id: String, time: Double, allocations: Double? = null, energy: Double? = null): String {
        val metrics = buildList {
            add("\"timeNs\": {\"iterations\": 8, \"runs\": [$time]}")
            allocations?.let { add("\"allocationCount\": {\"iterations\": 1, \"runs\": [$it]}") }
            energy?.let { add("\"energyJ\": {\"iterations\": 100, \"runs\": [$it], \"source\": \"rails\", \"kind\": \"measured\"}") }
        }
        return """{"runtime": {"model": "m"}, "cases": [{"id": "$id", "type": "T", "algorithm": "A", "provider": "P", "operation": "O",
                   "keySize": null, "inputSize": 64, "parameters": {}, "metrics": {${metrics.joinToString(", ")}}}]}"""
    }

    @Test
    fun timeComesFromTheTimingPassAndEachOwnedMetricFromItsPass() {
        val merged = PassMerge.merge(text("a", 10.0, allocations = 5.0), listOf(
            MetricSamples.ALLOCATIONS to text("a", 99.0, allocations = 2.0),
            MetricSamples.ENERGY to text("a", 77.0, energy = 1.5),
        ))
        val row = merged.rows.single()
        assertEquals(listOf(10.0), row.time?.runs)
        assertEquals(listOf(2.0), row.metrics[MetricSamples.ALLOCATIONS]?.runs)
        assertEquals(listOf(1.5), row.metrics[MetricSamples.ENERGY]?.runs)
        assertEquals(emptyList<String>(), merged.dropped)
    }

    @Test
    fun aCaseItsPassLostHasNoValueOfThatMetricRatherThanTheBasePasses() {
        val merged = PassMerge.merge(text("a", 10.0, allocations = 5.0), listOf(MetricSamples.ALLOCATIONS to text("b", 9.0, allocations = 2.0)))
        assertEquals(listOf(MetricSamples.TIME), merged.rows.single().metrics.keys.toList())
        assertEquals(listOf("not_merged: a: allocationCount: its pass has no row"), merged.dropped)
    }

    @Test
    fun anAllocationPassReadsOneRunPerSampleAndItsOwnSampleCount() {
        val example = File("example")
        val sampled = File(example, "benchmark_jetpack_example.json").readText()
            .replaceFirst("\"allocationCount\": {", "\"allocationSamples\": {\"runs\": [4.0, 4.0, 4.0]},\n        \"allocationCount\": {")
        val converted = JetpackResults.convert(sampled, File(example, "benchmark_prepared_example.yaml").readText(),
            pass = JetpackResults.PassView(metrics = listOf("TIME", "ALLOCATION"), samples = 3))
        val digest = converted.rows.single { it.algorithm == "SHA-256" }
        assertEquals(listOf(4.0, 4.0, 4.0), digest.metrics[MetricSamples.ALLOCATIONS]?.runs)
        assertEquals(true, converted.notApplied.none { it.startsWith("allocation_runs_changed: ${digest.id}") })
    }
}
