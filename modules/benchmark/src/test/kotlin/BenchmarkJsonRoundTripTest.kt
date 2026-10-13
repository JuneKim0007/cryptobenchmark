package io.github.junekim0007.cryptobench.benchmark

import io.github.junekim0007.cryptobench.benchmark.report.BenchmarkJson
import io.github.junekim0007.cryptobench.benchmark.report.Merge
import io.github.junekim0007.cryptobench.benchmark.report.MetricSamples
import io.github.junekim0007.cryptobench.benchmark.report.ReportedStats
import io.github.junekim0007.cryptobench.benchmark.report.ResultRow
import org.junit.Assert.assertEquals
import org.junit.Assert.assertThrows
import org.junit.Assert.assertTrue
import org.junit.Rule
import org.junit.Test
import org.junit.rules.TemporaryFolder

class BenchmarkJsonRoundTripTest {

    @get:Rule
    val output = TemporaryFolder()

    private fun text(rows: List<ResultRow>) = BenchmarkJson(output.root).text(runtime, rows)

    private fun row(id: String, metrics: Map<String, MetricSamples>) =
        ResultRow(id, "Cipher", "AES/GCM/NoPadding", "AndroidOpenSSL", "ENCRYPT", 128, 1024, "secret", metrics)

    private val runtime = mapOf("model" to "sdk_gphone64_arm64", "compilationMode" to "speed")

    private val both = linkedMapOf(
        MetricSamples.TIME to MetricSamples(listOf(1191.0, 1180.0, 1204.0), 8192),
        MetricSamples.ALLOCATIONS to MetricSamples(listOf(2.0, 2.0, 3.0), 1),
    )

    @Test
    fun whatTheWriterWritesIsWhatTheReaderReads() {
        val written = text(listOf(row("a", both)))

        val read = Merge.merge(listOf(written)).rows.single()

        assertEquals("a", read.id)
        assertEquals(both.keys.toList(), read.metrics.keys.toList())
        assertEquals(both.getValue(MetricSamples.TIME).runs, read.metrics.getValue(MetricSamples.TIME).runs)
        assertEquals(8192, read.metrics.getValue(MetricSamples.TIME).iterations)
        assertEquals(listOf(2.0, 2.0, 3.0), read.metrics.getValue(MetricSamples.ALLOCATIONS).runs)
        assertEquals(1, read.metrics.getValue(MetricSamples.ALLOCATIONS).iterations)
        assertEquals(128, read.keySize)
        assertEquals(1024, read.inputSize)
    }

    @Test
    fun twoWrittenProcessesMergeIntoOne() {
        val first = text(listOf(row("a", both)))
        val second = text(listOf(row("a", linkedMapOf(
            MetricSamples.TIME to MetricSamples(listOf(1300.0), 4096),
            MetricSamples.ALLOCATIONS to MetricSamples(listOf(4.0), 1),
        ))))

        val merged = Merge.merge(listOf(first, second))

        assertEquals(2, merged.processes)
        val row = merged.rows.single()
        assertEquals(listOf(1191.0, 1180.0, 1204.0, 1300.0), row.metrics.getValue(MetricSamples.TIME).runs)
        assertEquals(listOf(2.0, 2.0, 3.0, 4.0), row.metrics.getValue(MetricSamples.ALLOCATIONS).runs)
    }

    @Test
    fun aRowWithoutATimingIsRefusedWhereItIsBuilt() {
        val refused = assertThrows(IllegalArgumentException::class.java) {
            row("a", linkedMapOf(MetricSamples.ALLOCATIONS to MetricSamples(listOf(2.0), 1)))
        }
        assertEquals("missing_field: metrics.timeNs for a", refused.message)
    }

    @Test
    fun theLegacyPairAgreesWithTheTimingItDuplicates() {
        val written = text(listOf(row("a", both)))

        assertTrue(written, written.contains("\"iterations\": 8192"))
        assertTrue(written, written.contains("\"nanosPerOperation\": [1191.0, 1180.0, 1204.0]"))
        assertTrue(written, written.contains("\"timeNs\": {\"iterations\": 8192, \"runs\": [1191.0, 1180.0, 1204.0]}"))
    }

    @Test
    fun reportedStatisticsRoundTripForOneProcessAndAreDroppedByAMerge() {
        val reported = ReportedStats(1180.0, 1204.0, 1191.0, 0.011)
        val one = row("a", linkedMapOf(MetricSamples.TIME to MetricSamples(listOf(1191.0, 1180.0, 1204.0), 8192, reported)))
        val written = text(listOf(one))
        assertTrue(written, written.contains("\"reported\": {\"minimum\": 1180.0, \"maximum\": 1204.0, \"median\": 1191.0, \"coefficientOfVariation\": 0.011}"))
        assertEquals(reported, Merge.merge(listOf(written)).rows.single().time?.reported)
        assertEquals(null, Merge.merge(listOf(written, written)).rows.single().time?.reported)
    }

    @Test
    fun aSampleThatIsNotAFiniteNumberIsRefused() {
        assertEquals("not_finite: runs",
            org.junit.Assert.assertThrows(IllegalArgumentException::class.java) { MetricSamples(listOf(1.0, Double.NaN), 1) }.message)
        assertEquals("not_finite: reported statistics",
            org.junit.Assert.assertThrows(IllegalArgumentException::class.java) { ReportedStats(1.0, 2.0, 1.5, Double.POSITIVE_INFINITY) }.message)
    }
}
