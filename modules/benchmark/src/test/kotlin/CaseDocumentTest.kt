package io.github.junekim0007.cryptobench.benchmark

import io.github.junekim0007.cryptobench.benchmark.report.CaseDocument
import io.github.junekim0007.cryptobench.benchmark.report.MetricSamples
import org.junit.Assert.assertEquals
import org.junit.Assert.assertThrows
import org.junit.Test

class CaseDocumentTest {

    @Test
    fun aShapeThatIsNotACaseDocumentIsNamed() {
        val notAMapping = assertThrows(IllegalArgumentException::class.java) { CaseDocument.load("[1, 2]") }
        assertEquals("not_a_mapping: [1, 2]", notAMapping.message)
        val notAList = assertThrows(IllegalArgumentException::class.java) { CaseDocument.samples(7) }
        assertEquals("not_a_list: 7", notAList.message)
    }

    @Test
    fun aCaseMappingWithoutSizesStillBecomesARow() {
        val row = CaseDocument.row(
            mapOf("id" to "digest", "type" to "MessageDigest", "algorithm" to "SHA-256", "provider" to "SUN", "operation" to "DIGEST"),
            mapOf(MetricSamples.TIME to MetricSamples(listOf(10.0), CaseDocument.iterations(null))),
        )
        assertEquals(null, row.keySize)
        assertEquals(null, row.inputSize)
        assertEquals(1, row.time?.iterations)
    }

    @Test
    fun aMetricWithNoRunsIsNotAMeasurement() {
        val metrics = CaseDocument.metrics(
            mapOf(
                "timeNs" to mapOf("iterations" to 8192, "runs" to listOf(10.0)),
                "allocationCount" to mapOf("iterations" to 1, "runs" to emptyList<Double>()),
            ),
        )
        assertEquals(listOf("timeNs"), metrics.keys.toList())
        assertEquals(emptyMap<String, MetricSamples>(), CaseDocument.metrics(null))
    }
}
