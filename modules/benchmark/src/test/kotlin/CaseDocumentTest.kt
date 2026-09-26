package io.github.junekim0007.cryptobench.benchmark

import io.github.junekim0007.cryptobench.benchmark.report.CaseDocument
import org.junit.Assert.assertEquals
import org.junit.Assert.assertThrows
import org.junit.Test

/**
 * One reader for every file this module did not write: Jetpack's `benchmarkData.json`, preparation's
 * `prepared.yaml` and an earlier process's `benchmark.json`. A shape it does not recognise is named,
 * never coerced into a number, because the number would end up in the results as if it were measured.
 */
class CaseDocumentTest {

    @Test
    fun aShapeThatIsNotACaseDocumentIsNamed() {
        val notAMapping = assertThrows(IllegalArgumentException::class.java) { CaseDocument.load("[1, 2]") }
        assertEquals("not_a_mapping: [1, 2]", notAMapping.message)
        val notAList = assertThrows(IllegalArgumentException::class.java) { CaseDocument.samples(7) }
        assertEquals("not_a_list: 7", notAList.message)
    }

    /** A missing count is one call per sample, and a missing size is unknown — not zero. */
    @Test
    fun aCaseMappingWithoutSizesStillBecomesARow() {
        val row = CaseDocument.row(
            mapOf("id" to "digest", "type" to "MessageDigest", "algorithm" to "SHA-256", "provider" to "SUN", "operation" to "DIGEST"),
            CaseDocument.iterations(null),
            listOf(10L),
        )
        assertEquals(null, row.keySize)
        assertEquals(null, row.inputSize)
        assertEquals(1, row.iterations)
    }
}
