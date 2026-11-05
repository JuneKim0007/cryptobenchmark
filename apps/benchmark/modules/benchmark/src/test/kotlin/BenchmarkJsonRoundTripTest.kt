package io.github.junekim0007.cryptobench.benchmark

import io.github.junekim0007.cryptobench.benchmark.report.BenchmarkJson
import io.github.junekim0007.cryptobench.benchmark.report.Merge
import io.github.junekim0007.cryptobench.benchmark.report.MetricSamples
import io.github.junekim0007.cryptobench.benchmark.report.PassMerge
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
        ResultRow(id, "Cipher", "AES/GCM/NoPadding", "AndroidOpenSSL", "ENCRYPT", 128, 1024, "secret", metrics, emptyMap())

    private val runtime = mapOf("model" to "sdk_gphone64_arm64", "compilationMode" to "speed")

    private val both = linkedMapOf(
        MetricSamples.TIME to MetricSamples(listOf(1191.0, 1180.0, 1204.0), 8192),
        MetricSamples.ALLOCATIONS to MetricSamples(listOf(2.0, 2.0, 3.0), 1),
    )

    @Test
    fun aNameWithQuotesBackslashesOrControlCharactersStaysValidJson() {
        val odd = "P \"q\" \\ \n\t\u0001"
        val row = ResultRow("a", "Cipher", odd, odd, "ENCRYPT", null, null, null, both, mapOf(odd to odd))
        val written = BenchmarkJson(output.root).text(mapOf(odd to odd), listOf(row))
        assertTrue(written, written.contains("\"P \\\"q\\\" \\\\ \\n\\t\\u0001\""))
        val read = Merge.merge(listOf(written))
        assertEquals(odd, read.rows.single().provider)
        assertEquals(mapOf<String, Any>(odd to odd), read.rows.single().parameters)
        assertEquals(mapOf(odd to odd), read.runtime)
    }

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

    private fun variant(id: String, variant: String?) =
        ResultRow(id, "Cipher", "AES/GCM/NoPadding", "AndroidOpenSSL", "ENCRYPT", 128, 1024, "secret", both, emptyMap(), variant = variant)

    @Test
    fun theVariantIsWrittenAndSurvivesAProcessMergeAndAPassMerge() {
        val written = text(listOf(variant("a_fixed", "fixed"), variant("a_notFixed", "notFixed"), variant("scope", null)))
        assertTrue(written, written.contains("\"keyKind\": \"secret\", \"variant\": \"notFixed\""))
        assertTrue(written, written.contains("\"variant\": null"))
        val expected = listOf("fixed", "notFixed", null)
        assertEquals(expected, Merge.merge(listOf(written, written)).rows.map { it.variant })
        assertEquals(expected, PassMerge.merge(written, listOf(MetricSamples.ALLOCATIONS to written)).rows.map { it.variant })
    }

    @Test
    fun processesThatDisagreeOnTheVariantDropTheCase() {
        val merged = Merge.merge(listOf(text(listOf(variant("a", "fixed"))), text(listOf(variant("a", "notFixed")))))
        assertEquals(emptyList<ResultRow>(), merged.rows)
        assertTrue(merged.dropped.single(), merged.dropped.single().startsWith("not_merged: a: different_variant: a"))
    }

    private val gcm = linkedMapOf<String, Any>("mode" to "GCM", "padding" to "NoPadding", "ivBytes" to 12, "tagBits" to 128, "keyBits" to 128)

    private fun withParameters(id: String, parameters: Map<String, Any>) =
        ResultRow(id, "Cipher", "AES/GCM/NoPadding", "AndroidOpenSSL", "ENCRYPT", 128, 1024, "secret", both, parameters)

    @Test
    fun resolvedParametersRoundTripAndSurviveAMerge() {
        val written = text(listOf(withParameters("a", gcm)))
        assertTrue(written, written.contains("\"parameters\": {\"mode\": \"GCM\", \"padding\": \"NoPadding\", \"ivBytes\": 12, \"tagBits\": 128, \"keyBits\": 128}"))
        assertEquals(gcm, Merge.merge(listOf(written, written)).rows.single().parameters)
    }

    @Test
    fun processesThatResolvedDifferentParametersDropThatCaseAndTheOthersMerge() {
        val other = text(listOf(withParameters("a", gcm + ("ivBytes" to 16)), withParameters("b", gcm)))
        val merged = Merge.merge(listOf(text(listOf(withParameters("a", gcm), withParameters("b", gcm))), other, other))
        assertEquals(listOf("b"), merged.rows.map { it.id })
        assertEquals(1, merged.dropped.size)
        assertTrue(merged.dropped.single(), merged.dropped.single().startsWith("not_merged: a: different_parameters: a"))
    }

    @Test
    fun aProcessEntryWithoutParametersOrMetricsIsDroppedAndTheOtherProcessesKeepTheCase() {
        val written = text(listOf(row("a", both)))
        fun dropped(text: String) = Merge.merge(listOf(text, written)).let { it.dropped.single() to it.rows.single().time?.runs?.size }
        assertEquals("not_merged: a: process 1: missing_field: parameters for a" to 3, dropped(written.replace(", \"parameters\": {}", "")))
        assertEquals("not_merged: a: process 1: missing_field: metrics for a" to 3, dropped(written.replace(Regex(",\\n     \"metrics\": \\{.*\\}\\}"), "}")))
    }

    @Test
    fun aRowWithoutATimingIsRefusedWhereItIsBuilt() {
        val refused = assertThrows(IllegalArgumentException::class.java) {
            row("a", linkedMapOf(MetricSamples.ALLOCATIONS to MetricSamples(listOf(2.0), 1)))
        }
        assertEquals("missing_field: metrics.timeNs for a", refused.message)
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
